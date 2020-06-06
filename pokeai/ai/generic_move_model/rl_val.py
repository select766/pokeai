"""
強化学習モデルの強さを比較する
ランダムと対戦した勝率
"""

import os

# Prevent numpy from using multiple threads
from typing import List

import torch

from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.party_generator import Party

os.environ['OMP_NUM_THREADS'] = '1'  # NOQA

import argparse
import random
import numpy as np
from bson import ObjectId
from tqdm import tqdm
from pokeai.ai.rl_policy import RLPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj
from pokeai.ai.rating_battle import load_agent
from pokeai.util import yaml_load, pickle_dump, pickle_load


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


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("trainer_state")
    parser.add_argument("party_tags", help="学習対象のパーティのタグ(カンマ区切り)")
    parser.add_argument("--battles", type=int, default=100)
    args = parser.parse_args()
    parties = []
    # party_tagsのいずれかのタグを含むエージェントを列挙
    for party_doc in col_party.find({"tags": {"$in": args.party_tags.split(",")}}):
        parties.append(party_doc["party"])
    trainer = Trainer({}, {})
    trainer.load_state(pickle_load(args.trainer_state))

    sim = Sim()
    agent_scores = []
    for battle_idx in tqdm(range(args.battles)):
        target_parties = random.sample(parties, 2)
        agent_score = battle_once(sim, trainer, target_parties)
        agent_scores.append(agent_score)
    print("mean score", np.mean(agent_scores))


if __name__ == '__main__':
    main()
