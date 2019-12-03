"""
パーティ同士を対戦させてレーティングを計算する
"""

import os
import argparse
from typing import List, Tuple
import numpy as np
from bson import ObjectId
from logging import getLogger

from pokeai.ai.common import load_agent
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.util import pickle_dump

logger = getLogger(__name__)


def match_agents(sim, parties, policies):
    bsps = []
    for i in [0, 1]:
        bsp = BattleStreamProcessor()
        bsp.set_policy(policies[i])
        bsps.append(bsp)
    sim.set_processor(bsps)
    sim.set_party(parties)
    result = sim.run()
    winner = {'p1': 0, 'p2': 1, '': -1}[result['winner']]
    return winner


def rating_battle(parties, policies, agent_ids, match_count: int, fixed_rates: List[float] = None) -> Tuple[
    List[float], list]:
    """
    パーティ同士を多数戦わせ、レーティングを算出する。
    :param parties:
    :param policies:
    :param match_count: 1エージェント当たりの対戦回数
    :param fixed_rates: 各パーティの固定レート。固定されてないパーティは0。
    :return: パーティのレーティングおよび対戦ログ
    """
    assert len(parties) == len(policies)
    assert len(fixed_rates) == len(parties)
    sim = Sim()

    # レート初期値設定
    rates = np.full((len(parties),), 1500.0)
    for i in range(len(parties)):
        fr = fixed_rates[i]
        if fr != 0:
            rates[i] = fr

    log = []
    for i in range(match_count):
        # 対戦相手を決める
        # レーティングに乱数を加算し、ソートして隣接パーティ同士を戦わせる
        rates_with_random = rates + np.random.normal(scale=200., size=rates.shape)
        ranking = np.argsort(rates_with_random)
        for j in range(0, len(parties), 2):
            if j + 1 >= len(parties):
                # 奇数個パーティがある場合
                break
            left = ranking[j]
            right = ranking[j + 1]
            if fixed_rates[left] != 0 and fixed_rates[right] != 0:
                # どちらもレート固定パーティなので、対戦不要
                continue
            logger.debug(f"match start: {agent_ids[left]}, {agent_ids[right]}")
            winner = match_agents(sim, [parties[left], parties[right]], [policies[left], policies[right]])
            # レートを変動させる
            if winner >= 0:
                left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0))
                if winner == 0:
                    left_incr = 32 * (1.0 - left_winrate)
                else:
                    left_incr = 32 * (-left_winrate)
                if fixed_rates[left] == 0:
                    rates[left] += left_incr
                if fixed_rates[right] == 0:
                    rates[right] -= left_incr
            log.append({"agents": [agent_ids[left], agent_ids[right]],
                        "winner": winner})
            logger.debug(f"match end: winner: {winner}")
        abs_mean_diff = np.mean(np.abs(rates - 1500.0))
        logger.info(f"{i} rate mean diff: {abs_mean_diff}")
    return rates.tolist(), log


def main():
    import logging
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_tags", help="エージェントのタグ(カンマ区切り)")
    parser.add_argument("--fixed_rate", help="レート固定パーティのレートid")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    parser.add_argument("--log", help="ログディレクトリ")
    parser.add_argument("--loglevel", help="対戦経過のログ出力のレベル", choices=["INFO", "WARNING", "DEBUG"], default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))
    parties = []
    policies = []
    agent_ids = []
    fixed_rates = []
    rate_id = ObjectId()
    if args.log:
        os.makedirs(args.log, exist_ok=True)
    print(f"rate_id: {rate_id}")
    if args.fixed_rate:
        fixed_rate_map = col_rate.find_one({'_id': ObjectId(args.fixed_rate)})['rates']
    else:
        fixed_rate_map = {}
    # agent_tagsのいずれかのタグを含むエージェントを列挙
    for agent_doc in col_agent.find({"tags": {"$in": args.agent_tags.split(",")}}):
        party, policy = load_agent(agent_doc)
        parties.append(party)
        policies.append(policy)
        agent_ids.append(agent_doc['_id'])
        fixed_rates.append(fixed_rate_map.get(agent_doc['_id'], 0.0))
    rates, log = rating_battle(parties, policies, agent_ids, args.match_count, fixed_rates=fixed_rates)
    col_rate.insert_one({
        "_id": rate_id,
        "rates": {str(agent_id): rate for agent_id, rate in zip(agent_ids, rates)},
    })
    print(f"rate_id: {rate_id}")
    if args.log:
        pickle_dump(log, os.path.join(args.log, f"rate_{rate_id}.bin"))


if __name__ == '__main__':
    main()
