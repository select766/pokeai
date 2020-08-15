"""
パーティ共通モデルでの強化学習

"""

import os
from typing import List
import torch

from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.party_generator import Party

import argparse
import random
import numpy as np
from bson import ObjectId
from tqdm import tqdm
from pokeai.ai.rl_policy import RLPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.ai.party_db import col_party, col_trainer, pack_obj, unpack_obj
from pokeai.util import yaml_load


def battle_once(sim, trainer: Trainer, target_parties: List[Party]) -> float:
    agent = trainer.get_val_agent()
    bsp_t = BattleStreamProcessor()
    bsp_t.set_policy(RLPolicy(agent))
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


def train_episode(sim, trainer: Trainer, target_parties: List[Party]):
    agents = []
    bsps = []
    for player in range(2):
        agent = trainer.get_train_agent()
        bsp = BattleStreamProcessor()
        bsp.set_policy(RLPolicy(agent))
        agents.append(agent)
        bsps.append(bsp)
    sim.set_processor(bsps)
    sim.set_party(target_parties)
    with torch.no_grad():
        battle_result = sim.run()
    for player in range(2):
        trainer.extend_replay_buffer(agents[player]._replay_buffer)
    trainer.train()


def calc_save_at(n_battles, n_split):
    # n_battles == 50, n_split = 5なら
    # battle_idx == 9, 19, 29, 39, 49 のときに保存したい
    battle_idxs = []
    for battle_idx in np.linspace(0, n_battles, n_split + 1)[1:]:
        battle_idxs.append(int(battle_idx) - 1)
    return battle_idxs


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("train_param_file")
    parser.add_argument("--trainer_id", help="カンマ区切りでtrainer_idを複数指定すると一定間隔で保存する")
    parser.add_argument("--resume_trainer_id")
    args = parser.parse_args()
    if args.trainer_id is not None:
        trainer_ids = [ObjectId(p) for p in args.trainer_id.split(',')]
    else:
        trainer_ids = [ObjectId()]
    train_params = yaml_load(args.train_param_file)
    save_ats = calc_save_at(train_params["battles"], len(trainer_ids))
    tags = train_params["tags"]
    parties = []
    # party_tagsのいずれかのタグを含むエージェントを列挙
    for party_doc in col_party.find({"tags": {"$in": train_params["party_tags"]}}):
        parties.append(party_doc["party"])
    trainer = Trainer(**train_params["trainer"])
    if args.resume_trainer_id:
        resume_trainer_doc = col_trainer.find_one({"_id": ObjectId(args.resume_trainer_id)})
        trainer.load_initial_model(unpack_obj(resume_trainer_doc["trainer_packed"])["model"])
    sim = Sim()
    for battle_idx in tqdm(range(train_params["battles"])):
        target_parties = random.sample(parties, 2)
        train_episode(sim, trainer, target_parties)
        if battle_idx % 1000 == 0:
            print("mean score", random_val(sim, trainer, parties, 100))
        if battle_idx in save_ats:
            trainer_id = trainer_ids[save_ats.index(battle_idx)]
            col_trainer.insert_one({
                "_id": trainer_id,
                "trainer_packed": pack_obj(trainer.save_state()),
                "train_params": train_params,
                "tags": tags,
            })
    print("trainer id", trainer_ids)


if __name__ == '__main__':
    main()
