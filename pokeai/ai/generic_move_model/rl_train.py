"""
パーティ共通モデルでの強化学習

"""

import argparse
import random
from typing import List

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
        sim.run()
    for player in range(2):
        trainer.extend_replay_buffer(agents[player]._replay_buffer)
    trainer.total_battles += 1
    trainer.train()


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
    for party_doc in col_party.find({"tags": {"$in": train_params["party_tags"]}}):
        parties.append(party_doc["party"])
    if args.resume:
        assert args.initialize_by_trainer is None
        trainer = Trainer.load_state(unpack_obj(fs_checkpoint.get_last_version(str(trainer_id)).read()), resume=True)
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
        target_parties = random.sample(parties, 2)
        train_episode(sim, trainer, target_parties, surrogate_reward_config)
        if battle_idx % 1000 == 0:
            print("mean score", random_val(sim, trainer, parties, 100))
        if battle_idx % train_params["checkpoint_per_battles"] == (train_params["checkpoint_per_battles"] - 1):
            fs_checkpoint.put(pack_obj(trainer.save_state(resume=True)), filename=str(trainer_id),
                              metadata={"battles": trainer.total_battles})


if __name__ == '__main__':
    main()
