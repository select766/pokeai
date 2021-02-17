"""
パーティ共通モデルでの強化学習

"""

import argparse
import random
from typing import List, Tuple

import numpy as np
import torch
from bson import ObjectId
from tqdm import tqdm

from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import col_party, col_trainer, fs_checkpoint, pack_obj, unpack_obj
from pokeai.ai.random_policy import RandomPolicy
from pokeai.ai.rl_policy import RLPolicy
from pokeai.ai.surrogate_reward_config import SurrogateRewardConfigZero, SurrogateRewardConfig, \
    SurrogateRewardConfigDefaults
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.party_generator import Party
from pokeai.sim.sim import Sim
from pokeai.util import yaml_load


def battle_once(sim, trainer: Trainer, target_parties: List[Party]) -> float:
    agent = trainer.get_val_agent()
    bsp_t = BattleStreamProcessor()
    bsp_t.set_policy(RLPolicy(agent, SurrogateRewardConfigZero))
    bsp_o = BattleStreamProcessor()
    bsp_o.set_policy(RandomPolicy())
    sim.set_processor([bsp_t, bsp_o])
    sim.set_party(target_parties)
    with torch.no_grad():
        battle_result = sim.run()
    # player 1 = エージェント側の勝率
    return {'p1': 1.0, 'p2': 0.0, '': 0.5}[battle_result['winner']]


def random_val(sim, trainer: Trainer, parties: List[Party], battles: int) -> float:
    agent_scores = []
    for battle_idx in range(battles):
        target_parties = random.sample(parties, 2)
        agent_score = battle_once(sim, trainer, target_parties)
        agent_scores.append(agent_score)
    return float(np.mean(agent_scores))


def train_episode(sim, trainer: Trainer, target_parties: List[Party], surrogate_reward_config: SurrogateRewardConfig):
    agents = []
    bsps = []
    for player in range(2):
        agent = trainer.get_train_agent()
        bsp = BattleStreamProcessor()
        bsp.set_policy(RLPolicy(agent, surrogate_reward_config))
        agents.append(agent)
        bsps.append(bsp)
    sim.set_processor(bsps)
    sim.set_party(target_parties)
    with torch.no_grad():
        battle_result = sim.run()
    for player in range(2):
        trainer.extend_replay_buffer(agents[player]._replay_buffer)
    trainer.total_battles += 1
    trainer.train()
    return battle_result["winner"]  # 'p1', 'p2', '' (forcetieで引き分けの時)


def make_match_pairs(rates: List[float], random_std: float) -> List[Tuple[int, int]]:
    if random_std >= 0.0:
        rates_with_random = np.array(rates, dtype=np.float64)
        if random_std > 0.0:
            rates_with_random += np.random.normal(scale=random_std, size=rates_with_random.shape)
        idxs = np.argsort(rates_with_random).tolist()  # type: List[int]
    else:
        # レート無関係にランダム
        idxs = np.random.permutation(len(rates)).tolist()  # type: List[int]
    pairs = []
    for j in range(0, len(idxs), 2):
        if j + 1 >= len(idxs):
            # 奇数個パーティがある場合
            break
        pairs.append((idxs[j], idxs[j + 1]))
    random.shuffle(pairs)  # ソートしないとレート低い順になってしまい、学習順序が偏る
    return pairs


def update_rate(rates: List[float], match_pair: Tuple[int, int], winner: str):
    left, right = match_pair
    if winner != "":
        left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0))
        if winner == "p1":
            left_incr = 32 * (1.0 - left_winrate)
        else:
            assert winner == "p2"
            left_incr = 32 * (-left_winrate)
        rates[left] += left_incr
        rates[right] -= left_incr


def main():
    import logging
    parser = argparse.ArgumentParser()
    parser.add_argument("train_param_file")
    parser.add_argument("--initialize_by_trainer")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--loglevel", help="ログ出力(stderr)のレベル", choices=["INFO", "WARNING", "DEBUG"],
                        default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))
    train_params = yaml_load(args.train_param_file)
    trainer_id = ObjectId(train_params["trainer_id"])
    surrogate_reward_config = SurrogateRewardConfig(
        **dict(SurrogateRewardConfigDefaults, **train_params["surrogate_reward"]))
    tags = train_params["tags"]
    parties = []
    # party_tagsのいずれかのタグを含むパーティを列挙
    # 学習再開してもレート配列の順序を固定するためidでソートする
    for party_doc in col_party.find({"tags": {"$in": train_params["party_tags"]}}).sort("_id", 1):
        parties.append(party_doc["party"])
    match_pairs_queue = []
    rates = [1500.] * len(parties)
    if args.resume:
        assert args.initialize_by_trainer is None
        loaded_state_dict = unpack_obj(fs_checkpoint.get_last_version(str(trainer_id)).read())
        trainer = Trainer.load_state(loaded_state_dict, resume=True)
        rl_train_resume_info = loaded_state_dict.get("_rl_train", {})
        if "match_pairs_queue" in rl_train_resume_info:
            match_pairs_queue = rl_train_resume_info["match_pairs_queue"]
        if "rates" in rl_train_resume_info:
            rates = rl_train_resume_info["rates"]
        del loaded_state_dict
    else:
        if col_trainer.find_one({"_id": trainer_id}) is not None:
            print(f"trainer info for {trainer_id} already exists on db")
            return
        trainer = Trainer(**train_params["trainer"])
        if args.initialize_by_trainer:
            trainer_for_initialize = unpack_obj(fs_checkpoint.get_last_version(args.initialize_by_trainer).read())
            trainer.load_initial_model(trainer_for_initialize["model"])
            del trainer_for_initialize
        col_trainer.insert_one({
            "_id": trainer_id,
            "train_params": train_params,
            "tags": tags,
        })
    sim = Sim()
    for battle_idx in tqdm(range(trainer.total_battles, train_params["battles"])):
        if len(match_pairs_queue) == 0:
            match_pairs_queue = make_match_pairs(rates, train_params["match_config"]["random_std"])
        match_pair = match_pairs_queue.pop(0)
        winner = train_episode(sim, trainer, [parties[match_pair[0]], parties[match_pair[1]]], surrogate_reward_config)
        update_rate(rates, match_pair, winner)
        if battle_idx % 1000 == 0:
            print("mean score", random_val(sim, trainer, parties, 100))
        if battle_idx % train_params["checkpoint_per_battles"] == (train_params["checkpoint_per_battles"] - 1):
            save_state_dict = trainer.save_state(resume=True)
            # trainerに含まれていないが再開に必要な情報を格納
            save_state_dict["_rl_train"] = {"match_pairs_queue": match_pairs_queue, "rates": rates}
            fs_checkpoint.put(pack_obj(save_state_dict), filename=str(trainer_id),
                              metadata={"battles": trainer.total_battles})
            del save_state_dict


if __name__ == '__main__':
    main()
