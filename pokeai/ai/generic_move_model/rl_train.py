"""
パーティ共通モデルでの強化学習

"""

import os
from typing import List
import torch

from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.party_generator import Party

# Prevent numpy from using multiple threads
os.environ['OMP_NUM_THREADS'] = '1'  # NOQA

import argparse
import random
import numpy as np
from bson import ObjectId
from tqdm import tqdm
from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.rl_policy import RLPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj
from pokeai.ai.rating_battle import load_agent
from pokeai.util import yaml_load, pickle_dump


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


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party_tags", help="学習対象のパーティのタグ(カンマ区切り)")
    parser.add_argument("--battles", type=int, default=100)
    args = parser.parse_args()
    parties = []
    # party_tagsのいずれかのタグを含むエージェントを列挙
    for party_doc in col_party.find({"tags": {"$in": args.party_tags.split(",")}}):
        parties.append(party_doc["party"])
    trainer = Trainer({}, {})

    sim = Sim()
    for battle_idx in tqdm(range(args.battles)):
        target_parties = random.sample(parties, 2)
        train_episode(sim, trainer, target_parties)
        if battle_idx % 1000 == 0:
            print("mean score", random_val(sim, trainer, parties, 100))
    pickle_dump(trainer.save_state(), args.dst)


if __name__ == '__main__':
    main()