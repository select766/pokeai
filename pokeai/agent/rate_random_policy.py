"""
パーティ群をランダム戦略でレーティング
"""

import random
import argparse
from typing import Dict, List, Tuple
import copy
import pickle
import numpy as np
from tqdm import tqdm

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context
from pokeai.agent.common import match_random_policy
from pokeai.agent.util import load_pickle, save_pickle


def rating_battle(parties: List[Party], match_count: int) -> List[float]:
    """
    パーティ同士を多数戦わせ、レーティングを算出する。
    :param parties:
    :param match_count:
    :return: パーティのレーティング
    """
    assert len(parties) % 2 == 0
    rates = np.full((len(parties),), 1500.0)
    for i in range(match_count):
        # 対戦相手を決める
        # レーティングに乱数を加算し、ソートして隣接パーティ同士を戦わせる
        rates_with_random = rates + np.random.normal(scale=200., size=rates.shape)
        ranking = np.argsort(rates_with_random)
        for j in range(0, len(parties), 2):
            left = ranking[j]
            right = ranking[j + 1]
            winner = match_random_policy((parties[left], parties[right]))
            # レートを変動させる
            if winner >= 0:
                left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0))
                if winner == 0:
                    left_incr = 32 * (1.0 - left_winrate)
                else:
                    left_incr = 32 * (-left_winrate)
                rates[left] += left_incr
                rates[right] -= left_incr
        abs_mean_diff = np.mean(np.abs(rates - 1500.0))
        print(f"{i} rate mean diff: {abs_mean_diff}")
    return rates.tolist()  # type: List[float]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party_file")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    args = parser.parse_args()
    context.init()
    parties = load_pickle(args.party_file)["parties"]
    party_bodies = [p["party"] for p in parties]
    rates = rating_battle(party_bodies, args.match_count)
    uuid_rates = {p["uuid"]: r for p, r in zip(parties, rates)}
    save_pickle({"rates": uuid_rates}, args.dst)


if __name__ == '__main__':
    main()
