"""
山登り法でパーティ生成
"""

import random
import argparse
from typing import Dict, List, Tuple, Iterable, Optional
import numpy as np

from bson import ObjectId
from multiprocessing import Pool

from pokeai.agent.battle_agent_random import BattleAgentRandom
from pokeai.agent.battle_observer import BattleObserver
from pokeai.agent.party_db import load_party_group
from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim.party_template import PartyTemplate
from pokeai.sim import context
from pokeai.agent.util import load_pickle, save_pickle, reset_random, load_party_rate, load_yaml
from pokeai.agent import party_db
from pokeai.agent.battle_agents import load_agent
from pokeai.agent.rating_battle import rating_battle
from pokeai.agent.party_feature.party_rate_predictor import PartyRatePredictor


def load_benchmark_agents(rate_id):
    """
    ベンチマークとなるエージェントおよびレートをロードする
    :param rate_id:
    :return: エージェントリスト、レートリストのタプル
    """
    rate_info = party_db.col_rate.find_one({"_id": rate_id})
    rates = []
    agents = []
    for rate_obj in rate_info["rates"]:
        rates.append(rate_obj["rate"])
        agent_info = party_db.col_agent.find_one({"_id": rate_obj["agent_id"]})
        agents.append(load_agent(agent_info))
    return agents, rates


def hill_climbing_mp(kwargs):
    return hill_climbing(**kwargs)


benchmark_agents = None
benchmark_rates = None
party_rate_predictor = None  # type: PartyRatePredictor


def rate_party(match_count, party_t: PartyTemplate, observer):
    target_agent = BattleAgentRandom(ObjectId(), party_t, observer)
    agents = benchmark_agents.copy()  # shallow copy
    agents.append(target_agent)
    fixed_rates = benchmark_rates.copy()  # ベンチマークのパーティ群のレートは固定して、測定対象だけ可変
    fixed_rates.append(0)
    rates, _ = rating_battle(agents, match_count, fixed_rates)
    return rates[-1]


def hill_climbing(partygen: PartyGenerator, seed_party: PartyTemplate, neighbor: int,
                  pred_neighbor: int, iter: int, match_count: int, pred_only: bool,
                  history=False):
    """

    :param partygen:
    :param seed_party:
    :param neighbor: バトルでレートを測定する近傍数
    :param pred_neighbor: パーティ予測関数でレートを予測する近傍数。上位neighborがバトルに回る。0を指定すればパーティ予測関数を使わない。
    :param iter:
    :param match_count:
    :param pred_only: バトルを行わず、パーティ予測関数のみを使用する。pred_neighbor個のパーティからパーティ予測関数で上位1個を選択する処理となる。
    :param history:
    :return:
    """
    dummy_observer = BattleObserver(len(seed_party.poke_sts), [])  # ランダムエージェントでは不要なのでダミーを生成
    party = seed_party
    party.party_id = ObjectId()  # もしも山登り法で良いパーティができなかった場合、このパーティを結果として出力する。idを変えないと重複してしまいエラーとなる。
    history_data = []

    if pred_only:
        party_rate = party_rate_predictor.predict([party])[0]
    else:
        party_rate = rate_party(match_count, party, dummy_observer)
    if history is not None:
        history_data.append((party, party_rate))
    for i in range(iter):
        neighbors = []
        neighbor_rates = []
        if pred_neighbor:
            # pred_neighbor個の近傍作成、party_rate_predictorで上位neighbor個抽出、バトルで最上位を選択
            pred_neighbors = []
            for n in range(pred_neighbor):
                pred_neighbors.append(partygen.generate_neighbor_party(party))
            pred_rates = party_rate_predictor.predict(pred_neighbors)
            if pred_only:
                top_idx = int(np.argmax(pred_rates))
                top_rate = pred_rates[top_idx]
                top_party = pred_neighbors[top_idx]
            else:
                for idx in np.argsort(pred_rates)[:-neighbor - 1:-1]:  # 逆順にneighbor個取得
                    neighbors.append(pred_neighbors[idx])
        else:
            for n in range(neighbor):
                neighbors.append(partygen.generate_neighbor_party(party))

        if not pred_only:
            for neighbor_party in neighbors:
                neighbor_rates.append(rate_party(match_count, neighbor_party, dummy_observer))
            top_idx = int(np.argmax(neighbor_rates))
            top_rate = neighbor_rates[top_idx]
            top_party = neighbors[top_idx]
        if top_rate > party_rate:
            party_rate = top_rate
            party = top_party
        if history:
            history_data.append((party, party_rate))
    print(party)
    print(f"rate: {party_rate}")
    return party, party_rate, history_data


def process_init(config):
    global benchmark_agents, benchmark_rates, party_rate_predictor
    reset_random()
    context.init()
    benchmark_agents, benchmark_rates = load_benchmark_agents(ObjectId(config["benchmark_rate_id"]))
    if config["party_rate_predictor"]:
        party_rate_predictor = load_pickle(config["party_rate_predictor"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("dst_party_group_tag")
    parser.add_argument("--history")
    parser.add_argument("-j", type=int, help="並列処理数")
    args = parser.parse_args()
    context.init()
    config = load_yaml(args.config)
    partygen = PartyGenerator(PartyRule[config["rule"]], **config["partygen"])
    seed_parties = load_party_group(config["seed_party_group"])
    results = []
    generated_parties = []
    with Pool(processes=args.j, initializer=process_init, initargs=(config,)) as pool:
        args_list = []
        for seed_party in seed_parties:
            job_kwargs = {"partygen": partygen, "history": bool(args.history), "seed_party": seed_party}
            job_kwargs.update(config["hill_climbing"])
            args_list.append(job_kwargs)
        for generated_party, rate, history_result in pool.imap_unordered(hill_climbing_mp, args_list):
            # 1サンプル生成ごとに呼ばれる(全計算が終わるまで待たない)
            generated_parties.append(generated_party)
            results.append(
                {"party": generated_party, "optimize_rate": rate, "history": history_result})
            print(f"completed {len(results)} / {len(seed_parties)}")
    party_db.save_party_group(generated_parties, args.dst_party_group_tag)
    if args.history:
        save_pickle(results, args.history)


if __name__ == '__main__':
    main()
