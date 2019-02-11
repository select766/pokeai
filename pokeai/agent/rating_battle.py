"""
パーティ同士を対戦させてレーティングを計算する
"""

import argparse
from typing import List, Tuple
import numpy as np
from bson import ObjectId

from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_agents import load_agent
from pokeai.agent.common import match_agents
from pokeai.agent.util import save_pickle
from pokeai.sim import context
from pokeai.agent import party_db


def rating_battle(agents: List[BattleAgent], match_count: int, fixed_rates: List[float] = None,
                  take_log: bool = False) -> Tuple[List[float], list]:
    """
    パーティ同士を多数戦わせ、レーティングを算出する。
    :param agents:
    :param match_count: 1エージェント当たりの対戦回数
    :param fixed_rates: 各パーティの固定レート。固定されてないパーティは0。
    :return: パーティのレーティングおよび対戦ログ
    """
    if fixed_rates is None:
        fixed_rates = [0] * len(agents)
    assert len(fixed_rates) == len(agents)

    # レート初期値設定
    rates = np.full((len(agents),), 1500.0)
    for i in range(len(agents)):
        fr = fixed_rates[i]
        if fr != 0:
            rates[i] = fr

    log = []
    for i in range(match_count):
        # 対戦相手を決める
        # レーティングに乱数を加算し、ソートして隣接パーティ同士を戦わせる
        rates_with_random = rates + np.random.normal(scale=200., size=rates.shape)
        ranking = np.argsort(rates_with_random)
        for j in range(0, len(agents), 2):
            if j + 1 >= len(agents):
                # 奇数個パーティがある場合
                break
            left = ranking[j]
            right = ranking[j + 1]
            if fixed_rates[left] != 0 and fixed_rates[right] != 0:
                # どちらもレート固定パーティなので、対戦不要
                continue
            log_objs = None
            log_func = None
            if take_log:
                log_objs = []
                log_func = lambda record: log_objs.append(record)
            winner = match_agents([agents[left], agents[right]], logger=log_func)
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
            if take_log:
                log.append({"agents": [agents[left].agent_id, agents[right].agent_id],
                            "winner": winner, "log": log_objs})
        abs_mean_diff = np.mean(np.abs(rates - 1500.0))
        print(f"{i} rate mean diff: {abs_mean_diff}")
    return rates.tolist(), log


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agent_tags", help="エージェントのタグ(カンマ区切り)")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    args = parser.parse_args()
    context.init()
    agents = []
    for agent_info in party_db.col_agent.find({"tags": {"$in": args.agent_tags.split(",")}}):
        agents.append(load_agent(agent_info))
    rates, log = rating_battle(agents, args.match_count, take_log=True)
    rate_id = ObjectId()
    rate_info = []
    for agent, rate in zip(agents, rates):
        rate_info.append({"agent_id": agent.agent_id, "rate": rate})
    party_db.col_rate.insert_one({
        "_id": rate_id,
        "rates": rate_info,
    })
    save_pickle(log, f"rating_battle_log_{rate_id}.bin")
    print(f"rate_id: {rate_id}")


if __name__ == '__main__':
    main()
