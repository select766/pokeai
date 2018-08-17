"""
ポケモンおよび技の価値を推定する。
パーティのレーティング情報を入力とし、当該ポケモンまたは技を含んでいるパーティのレーティング平均を計算。
レーティング-1500を価値として出力。
"""

import random
import argparse
from typing import Dict, List, Tuple, Iterable, Optional
import copy
import pickle
import numpy as np
from collections import defaultdict

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.move_info_db import move_info_db
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context
from pokeai.agent.common import match_random_policy
from pokeai.agent.util import load_pickle, save_pickle, reset_random, load_party_rate


def get_average_rate(parties: List[Party], rates: np.ndarray):
    key_scores = {}
    for dexno in Dexno:
        key_scores[dexno] = []
    for move in Move:
        key_scores[move] = []
    for party, rate in zip(parties, rates):
        for poke in party.pokes:
            st = poke._poke_st
            key_scores[st.dexno].append(rate)
            for move in st.moves:
                key_scores[move].append(rate)
    avg = {}
    std = {}
    for key, scores in key_scores.items():
        if len(scores) == 0:
            avg[key] = 0.0
            std[key] = 0.0
        else:
            avg[key] = float(np.mean(scores) - 1500.0)
            std[key] = float(np.std(scores))
    return {"avg": avg, "std": std}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party_pool", help="レーティング測定相手パーティ群")
    parser.add_argument("party_rate", help="レーティング測定相手パーティ群のレーティング")
    args = parser.parse_args()
    context.init()
    parties, rates = load_party_rate(args.party_pool, args.party_rate)
    stats = get_average_rate(parties, rates)
    save_pickle(stats, args.dst)


if __name__ == '__main__':
    main()
