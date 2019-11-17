"""
与えられたパーティ群にランダム戦略でバトルさせて勝敗を記録する
"""

import argparse
from typing import List
from tqdm import tqdm

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
    for i in [0, 1]:
        bsp = BattleStreamProcessor()
        bsp.set_policy(RandomPolicy())
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
