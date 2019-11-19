"""
与えられたパーティ群にランダム戦略でバトルさせて勝敗を記録する
"""

import argparse
from typing import List
from tqdm import tqdm

from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.linear_model import LinearModel
from pokeai.ai.linear_policy import LinearPolicy
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.party_generator import Party
from pokeai.sim.sim import Sim
from pokeai.util import pickle_load, pickle_dump


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("parties")
    parser.add_argument("dst")
    args = parser.parse_args()
    parties = pickle_load(args.parties)  # type: List[Party]
    sim = Sim()
    bsps = []
    feature_extractor = FeatureExtractor()
    for i in [0, 1]:
        bsp = BattleStreamProcessor()
        if True:
            model = LinearModel(feature_dims=feature_extractor.get_dims(), action_dims=18)
            policy = LinearPolicy(feature_extractor, model)
        else:
            policy = RandomPolicy()
        bsp.set_policy(policy)
        bsps.append(bsp)
    sim.set_processor(bsps)
    results = []
    for i in tqdm(range(len(parties))):
        for j in range(i + 1, len(parties)):
            sim.set_party([parties[i], parties[j]])
            result = sim.run()
            results.append({"party_idxs": [i, j], "result": result})
    pickle_dump(results, args.dst)


if __name__ == '__main__':
    main()
