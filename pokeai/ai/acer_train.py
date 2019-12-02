"""
A3Cによる行動学習のプロトタイプ
入力
- 対戦相手のエージェント群(tag)
- 戦略を学習するパーティのid

出力
- エージェントの保存
"""

import os

# Prevent numpy from using multiple threads
os.environ['OMP_NUM_THREADS'] = '1'  # NOQA

import argparse
import random
import numpy as np
from bson import ObjectId
from tqdm import tqdm
from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.rl_policy import RLPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj
from pokeai.ai.rating_battle import load_agent
from pokeai.util import yaml_load


def acer_train(sim, target_policy, target_party, fitness_policies, fitness_parties) -> float:
    opponent_idx = random.randrange(len(fitness_parties))
    bsp_t = BattleStreamProcessor()
    bsp_t.set_policy(target_policy)
    bsp_o = BattleStreamProcessor()
    bsp_o.set_policy(fitness_policies[opponent_idx])
    sim.set_processor([bsp_t, bsp_o])
    sim.set_party([target_party, fitness_parties[opponent_idx]])
    battle_result = sim.run()
    return {'p1': 1.0, 'p2': 0.0, '': 0.5}[battle_result['winner']]


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("party_id", help="学習対象のパーティID")
    parser.add_argument("agent_tags", help="対戦相手エージェントのタグ(カンマ区切り)")
    parser.add_argument("agent_params", help="エージェントのモデル構造パラメータファイル")
    parser.add_argument("dst_agent_tags")
    parser.add_argument("--battles", type=int, default=100)
    parser.add_argument("--step_agent_tags", help="途中のエージェントを保存するタグ")
    parser.add_argument("--save_step", help="途中のエージェントを保存する頻度（バトル数）", type=int, default=0)
    args = parser.parse_args()
    if args.save_step:
        assert args.step_agent_tags
    fitness_parties = []
    fitness_policies = []
    # agent_tagsのいずれかのタグを含むエージェントを列挙
    for agent_doc in col_agent.find({"tags": {"$in": args.agent_tags.split(",")}}):
        party, policy = load_agent(agent_doc)
        fitness_parties.append(party)
        fitness_policies.append(policy)
    target_party_doc = col_party.find_one({'_id': ObjectId(args.party_id)})
    target_party = target_party_doc['party']

    feature_extractor = FeatureExtractor()
    target_policy = RLPolicy(feature_extractor, yaml_load(args.agent_params))
    target_policy.train = True
    sim = Sim()
    results = []

    def save(policy_to_save, tags, battle_results):
        trained_agent_id = ObjectId()
        col_agent.insert_one({
            '_id': trained_agent_id,
            'party_id': target_party_doc['_id'],
            'policy_packed': pack_obj(policy_to_save),
            'tags': tags,
            'battle_results': battle_results,
            'steps': len(battle_results),
        })
        return trained_agent_id

    for battle_idx in tqdm(range(args.battles)):
        results.append(acer_train(sim, target_policy, target_party, fitness_policies, fitness_parties))

        if args.save_step and battle_idx > 0 and len(results) % args.save_step == 0:
            target_policy.train = False
            save(target_policy, args.step_agent_tags.split(','), results)
            target_policy.train = True
        if battle_idx % 100 == 100 - 1:
            print(f"mean win rate in recent 100 battles: {np.mean(results[-100:])}")
    target_policy.train = False
    final_agent_id = save(target_policy, args.dst_agent_tags.split(','), results)
    target_policy.train = True
    print(f"trained agent id: {final_agent_id}")


if __name__ == '__main__':
    main()
