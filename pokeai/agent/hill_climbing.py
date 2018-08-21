"""
山登り法でパーティ生成
"""

import random
import argparse
from typing import Dict, List, Tuple, Iterable, Optional
import copy
import pickle
import numpy as np
import uuid
from tqdm import tqdm
from multiprocessing import Pool

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
from pokeai.agent.util import load_pickle, save_pickle, reset_random, load_party_rate, load_yaml


def rating_single_party(target_party: Party, parties: List[Party], party_rates: np.ndarray, match_count: int,
                        initial_rate: float = 1500.0,
                        reject_rate: float = 0.0) -> float:
    """
    あるパーティを、レーティングが判明している別パーティ群と戦わせてレーティングを計算する。
    :return: パーティのレーティング
    """
    rate = initial_rate
    for i in range(match_count):
        # 対戦相手を決める
        rate_with_random = rate + np.random.normal(scale=200.)
        # 対戦相手にもランダムに値を加算する。さもないと、rateが十分高い場合に最上位の相手としか当たらなくなる。
        party_rates_with_random = party_rates + np.random.normal(scale=200., size=party_rates.shape)
        nearest_party_idx = int(np.argmin(np.abs(party_rates_with_random - rate_with_random)))
        winner = match_random_policy((target_party, parties[nearest_party_idx]))
        # レートを変動させる
        if winner >= 0:
            left_winrate = 1.0 / (1.0 + 10.0 ** ((party_rates[nearest_party_idx] - rate) / 400.0))
            if winner == 0:
                left_incr = 32 * (1.0 - left_winrate)
            else:
                left_incr = 32 * (-left_winrate)
            rate += left_incr
            if rate < reject_rate:
                # 明らかに弱く、山登り法で採用の可能性がない場合に打ち切る
                break
    return rate


def hill_climbing_mp(args):
    return hill_climbing(*args)


def hill_climbing(partygen: PartyGenerator, seed_party, baseline_parties, baseline_rates, neighbor: int, iter: int,
                  match_count: int,
                  history: Optional[list] = None):
    party = seed_party
    party_rate = rating_single_party(party, baseline_parties, baseline_rates, match_count, 0.0)
    if history is not None:
        history.append((party, party_rate))
    for i in range(iter):
        neighbors = []
        neighbor_rates = []
        for n in range(neighbor):
            new_party = partygen.generate_neighbor_party(party)
            new_rate = rating_single_party(new_party, baseline_parties, baseline_rates, match_count, party_rate,
                                           party_rate - 400.0)
            neighbors.append(new_party)
            neighbor_rates.append(new_rate)
        print(f"{i} rates: {neighbor_rates}")
        best_neighbor_idx = int(np.argmax(neighbor_rates))
        if neighbor_rates[best_neighbor_idx] > party_rate:
            party_rate = neighbor_rates[best_neighbor_idx]
            party = neighbors[best_neighbor_idx]
        if history is not None:
            history.append((party, party_rate))
    print(party)
    print(f"rate: {party_rate}")
    return party, party_rate, history


def process_init():
    reset_random()
    context.init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("seed_party", help="更新元になるパーティ群")
    parser.add_argument("baseline_party_pool", help="レーティング測定相手パーティ群")
    parser.add_argument("baseline_party_rate", help="レーティング測定相手パーティ群のレーティング")
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--rule_params")
    parser.add_argument("--neighbor", type=int, default=10, help="生成する近傍パーティ数")
    parser.add_argument("--iter", type=int, default=100, help="iteration数")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("-j", type=int, help="並列処理数")
    args = parser.parse_args()
    context.init()
    baseline_parties, baseline_rates = load_party_rate(args.baseline_party_pool, args.baseline_party_rate)
    rule_params = load_yaml(args.rule_params) if args.rule_params else {}
    partygen = PartyGenerator(PartyRule[args.rule], **rule_params)
    seed_parties = [p["party"] for p in load_pickle(args.seed_party)["parties"]]
    results = []
    with Pool(processes=args.j, initializer=process_init) as pool:
        args_list = []
        for seed_party in seed_parties:
            history = [] if args.history else None
            args_list.append((partygen, seed_party, baseline_parties, baseline_rates, args.neighbor, args.iter,
                              args.match_count, history))
        for generated_party, rate, history_result in pool.imap_unordered(hill_climbing_mp, args_list):
            # 1サンプル生成ごとに呼ばれる(全計算が終わるまで待たない)
            results.append(
                {"party": generated_party, "uuid": str(uuid.uuid4()), "optimize_rate": rate, "history": history_result})
            print(f"completed {len(results)} / {len(seed_parties)}")
    save_pickle({"parties": results}, args.dst)


if __name__ == '__main__':
    main()
