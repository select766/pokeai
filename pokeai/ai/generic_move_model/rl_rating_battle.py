"""
パーティ同士を対戦させてレーティングを計算する
暫定的に、1つのモデルだけを対象にしてパーティの組み合わせだけ変える
"""

import os
import argparse
from typing import List, Tuple
import numpy as np
import torch
from bson import ObjectId
from logging import getLogger

from pokeai.ai.common import load_agent
from pokeai.ai.generic_move_model.trainer import Trainer
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from pokeai.ai.random_policy import RandomPolicy
from pokeai.ai.rl_policy import RLPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.util import pickle_dump, pickle_load

logger = getLogger(__name__)


def match_agents(sim, parties, policies):
    bsps = []
    for i in [0, 1]:
        bsp = BattleStreamProcessor()
        bsp.set_policy(policies[i])
        bsps.append(bsp)
    sim.set_processor(bsps)
    sim.set_party(parties)
    with torch.no_grad():
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
    parser.add_argument("trainer_state")
    parser.add_argument("party_tags", help="学習対象のパーティのタグ(カンマ区切り)")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    parser.add_argument("--log", help="ログディレクトリ")
    parser.add_argument("--loglevel", help="対戦経過のログ出力のレベル", choices=["INFO", "WARNING", "DEBUG"], default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.loglevel))
    agent_ids = []
    rate_id = ObjectId()
    if args.log:
        os.makedirs(args.log, exist_ok=True)
    print(f"rate_id: {rate_id}")
    parties = []
    # party_tagsのいずれかのタグを含むエージェントを列挙
    for party_doc in col_party.find({"tags": {"$in": args.party_tags.split(",")}}):
        parties.append(party_doc["party"])
        agent_ids.append(party_doc["_id"])
    if args.trainer_state:
        trainer = Trainer({"n_layers": 3, "n_channels": 16, "bn": False}, {})
        trainer.load_state(pickle_load(args.trainer_state))
        policy = RLPolicy(trainer.get_val_agent())
    else:
        # 比較用ランダム行動版
        policy = RandomPolicy()
    policies = [policy] * len(parties)
    fixed_rates = [0.0] * len(parties)  # 未使用
    rates, log = rating_battle(parties, policies, agent_ids, args.match_count, fixed_rates=fixed_rates)
    print(f"rate_id: {rate_id}")
    if args.log:
        pickle_dump({
            "_id": rate_id,
            "rates": {str(agent_id): rate for agent_id, rate in zip(agent_ids, rates)},
        }, os.path.join(args.log, f"rate_table_{rate_id}.bin"))
        pickle_dump(log, os.path.join(args.log, f"rate_{rate_id}.bin"))


if __name__ == '__main__':
    main()
