"""
A3Cによる行動学習のプロトタイプ
グループ内のエージェント同士が対戦して全エージェントが更新されていく
入力
- 戦略を学習するパーティ群のタグ

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


def a3c_group_train(target_policies, target_parties, battles: int):
    sim = Sim()
    for gen in tqdm(range(battles)):
        matches = list(range(len(target_policies)))
        random.shuffle(matches)
        for i in range(0, len(matches), 2):
            p_0 = matches[i]
            p_1 = matches[i + 1]
            bsp_0 = BattleStreamProcessor()
            bsp_0.set_policy(target_policies[p_0])
            bsp_1 = BattleStreamProcessor()
            bsp_1.set_policy(target_policies[p_1])
            sim.set_processor([bsp_0, bsp_1])
            sim.set_party([target_parties[p_0], target_parties[p_1]])
            battle_result = sim.run()


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("party_tags", help="学習対象パーティのタグ(カンマ区切り)")
    parser.add_argument("agent_params", help="エージェントのモデル構造パラメータファイル")
    parser.add_argument("dst_agent_tags")
    parser.add_argument("--battles", type=int, default=100)
    args = parser.parse_args()
    agent_params = yaml_load(args.agent_params)
    feature_extractor = FeatureExtractor()
    target_parties = []
    target_party_ids = []
    target_policies = []
    # party_tagsのいずれかのタグを含むパーティを列挙
    for target_party_doc in col_party.find({"tags": {"$in": args.party_tags.split(",")}}):
        target_party_ids.append(target_party_doc['_id'])
        target_party = target_party_doc['party']
        target_policy = RLPolicy(feature_extractor, agent_params)
        target_policy.train = True
        target_parties.append(target_party)
        target_policies.append(target_policy)
    a3c_group_train(target_policies, target_parties, args.battles)
    dst_agent_tags = args.dst_agent_tags.split(',')
    for party_id, policy in zip(target_party_ids, target_policies):
        policy.train = False
        trained_agent_id = ObjectId()
        col_agent.insert_one({
            '_id': trained_agent_id,
            'party_id': party_id,
            'policy_packed': pack_obj(policy),
            'tags': dst_agent_tags
        })
    print("saved agents")


if __name__ == '__main__':
    main()
