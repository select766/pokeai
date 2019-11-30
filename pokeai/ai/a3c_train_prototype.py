"""
A3Cによる行動学習のプロトタイプ
入力
- 対戦相手のエージェント群(tag)
- 戦略を学習するパーティのid

出力
- エージェントの保存
"""

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


def a3c_train(target_policy, target_party, fitness_policies, fitness_parties, battles: int):
    sim = Sim()
    results = []
    for gen in tqdm(range(battles)):
        opponent_idx = random.randrange(len(fitness_parties))
        bsp_t = BattleStreamProcessor()
        bsp_t.set_policy(target_policy)
        bsp_o = BattleStreamProcessor()
        bsp_o.set_policy(fitness_policies[opponent_idx])
        sim.set_processor([bsp_t, bsp_o])
        sim.set_party([target_party, fitness_parties[opponent_idx]])
        battle_result = sim.run()
        results.append(1 if battle_result['winner'] == 'p1' else 0)
        if gen % 100 == 0:
            print(f"mean winrate: {np.mean(results[-100:])}")


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("party_id", help="学習対象のパーティID")
    parser.add_argument("agent_tags", help="エージェントのタグ(カンマ区切り)")
    parser.add_argument("agent_params", help="エージェントのモデル構造パラメータファイル")
    parser.add_argument("dst_agent_tags")
    parser.add_argument("--battles", type=int, default=100)
    args = parser.parse_args()
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
    a3c_train(target_policy, target_party, fitness_policies, fitness_parties, args.battles)
    target_policy.train = False
    trained_agent_id = ObjectId()
    col_agent.insert_one({
        '_id': trained_agent_id,
        'party_id': target_party_doc['_id'],
        'policy_packed': pack_obj(target_policy),
        'tags': args.dst_agent_tags.split(',')
    })
    print(f"trained agent id: {trained_agent_id}")


if __name__ == '__main__':
    main()
