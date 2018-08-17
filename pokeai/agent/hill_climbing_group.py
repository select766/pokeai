"""
山登り法でパーティ生成

対戦相手のパーティ群を固定せず、グループ内で相互に対戦させつつ各パーティを更新していく。
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
from pokeai.agent.util import load_pickle, save_pickle, reset_random
from pokeai.agent.rate_random_policy import rating_battle


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
        nearest_party_idx = int(np.argmin(np.abs(party_rates - rate_with_random)))
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


def randint_len(seq: list) -> int:
    top = len(seq)
    if top <= 0:
        raise ValueError("Sequence length <= 0")
    if top == 1:
        return 0
    # np.random.randint(0)はエラーとなる
    return int(np.random.randint(top - 1))


def generate_neighbor_party(party: Party, partygen: PartyGenerator) -> Party:
    assert len(party.pokes) == 1
    pokest = copy.deepcopy(party.pokes[0]._poke_st)
    moves = pokest.moves
    learnable_moves = partygen.db.get_leanable_moves(pokest.dexno, pokest.lv)
    for m in moves:
        learnable_moves.remove(m)
    if len(learnable_moves) == 0 and len(moves) == 1:
        # 技を1つしか覚えないポケモン(LV15未満のコイキング等)
        # どうしようもない
        pass
    elif len(learnable_moves) == 0 or (np.random.random() < 0.1 and len(moves) > 1):
        # 技を消す
        moves.pop(randint_len(moves))
    elif np.random.random() < 0.1 and len(moves) < 4:
        # 技を足す
        moves.append(learnable_moves[randint_len(learnable_moves)])
    else:
        # 技を変更する
        new_move = learnable_moves[randint_len(learnable_moves)]
        moves[randint_len(moves)] = new_move
    return Party([pokest])


def modify_and_find_best(partygen: PartyGenerator, party: Party, party_rate: float, baseline_parties, baseline_rates,
                         neighbor: int, match_count: int):
    """
    パーティを少し変化させて最良のものを選ぶ。改善がなければ元のパーティを返す。
    :param partygen:
    :param party:
    :param baseline_parties:
    :param baseline_rates:
    :param neighbor:
    :param match_count:
    :return:
    """
    neighbors = []
    neighbor_rates = []
    # 相手が変わっているので元のパーティもレーティングしなおす必要あり
    party_rate = rating_single_party(party, baseline_parties, baseline_rates, match_count, party_rate,
                                     party_rate - 400.0)
    for n in range(neighbor):
        new_party = generate_neighbor_party(party, partygen)
        new_rate = rating_single_party(new_party, baseline_parties, baseline_rates, match_count, party_rate,
                                       party_rate - 400.0)
        neighbors.append(new_party)
        neighbor_rates.append(new_rate)
    best_neighbor_idx = int(np.argmax(neighbor_rates))
    if neighbor_rates[best_neighbor_idx] > party_rate:
        party_rate = neighbor_rates[best_neighbor_idx]
        party = neighbors[best_neighbor_idx]
    return party, party_rate


def hill_climbing_group(partygen: PartyGenerator, baseline_parties, baseline_rates, neighbor: int, iter: int,
                        match_count: int):
    parties = baseline_parties
    party_rates = baseline_rates
    histories = [[{"party": parties[j], "rate": baseline_rates[j]}] for j in range(len(baseline_parties))]
    for i in range(iter):
        print(f"iteration {i}")
        next_parties = []
        for j in range(len(baseline_parties)):
            party, party_rate = modify_and_find_best(partygen, parties[j], party_rates[j], baseline_parties,
                                                     baseline_rates, neighbor, match_count)
            next_parties.append(party)
            print(f"rate: {party_rates[j]} => {party_rate}")
            print(parties[j])
            print("=>")
            print(party)
        # 新規パーティ同士でレーティング計算する(でないとレーティングがインフレするし、現在パーティに対するメタ戦略が異常に高いレーティングになる)
        print("rating between new parties")
        next_rates = rating_battle(next_parties, match_count)
        for j in range(len(baseline_parties)):
            histories[j].append({"party": next_parties[j], "party_rate": next_rates[j]})
        parties = next_parties
        party_rates = np.array(next_rates)

    return parties, party_rates, histories


def load_baseline_party_rate(parties_file, rates_file):
    parties = load_pickle(parties_file)["parties"]
    uuid_rates = load_pickle(rates_file)["rates"]
    party_bodies = []
    rates = []
    for party_data in parties:
        party_bodies.append(party_data["party"])
        rates.append(uuid_rates[party_data["uuid"]])
    return party_bodies, np.array(rates, dtype=np.float)


def process_init():
    reset_random()
    context.init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst_prefix")
    parser.add_argument("n_party", type=int)
    parser.add_argument("baseline_party_pool", help="初期パーティ群")
    parser.add_argument("baseline_party_rate", help="初期パーティ群のレーティング")
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--neighbor", type=int, default=10, help="生成する近傍パーティ数")
    parser.add_argument("--iter", type=int, default=100, help="iteration数")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    # parser.add_argument("-j", type=int, help="並列処理数")
    args = parser.parse_args()
    context.init()
    baseline_parties, baseline_rates = load_baseline_party_rate(args.baseline_party_pool, args.baseline_party_rate)
    partygen = PartyGenerator(PartyRule[args.rule])
    parties, party_rates, histories = hill_climbing_group(partygen, baseline_parties, baseline_rates, args.neighbor,
                                                          args.iter, args.match_count)
    results = []
    uuid_rates = {}
    for party, party_rate, history in zip(parties, party_rates, histories):
        party_uuid = str(uuid.uuid4())
        results.append({"party": party, "uuid": party_uuid, "history": history})
        uuid_rates[party_uuid] = party_rate
    save_pickle({"parties": results}, args.dst_prefix + ".bin")
    save_pickle({"rates": uuid_rates}, args.dst_prefix + "_rate.bin")


if __name__ == '__main__':
    main()
