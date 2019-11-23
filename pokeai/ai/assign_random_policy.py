"""
パーティにランダムエージェントをくっつける
"""

import argparse
from bson import ObjectId

from pokeai.ai.random_policy import RandomPolicy
from pokeai.ai.party_db import col_party, col_agent, pack_obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("party_tag", help="対象パーティのタグ")
    parser.add_argument("tags", help="エージェントに付与するタグ")
    args = parser.parse_args()
    tags = args.tags.split(",") if args.tags else []
    agent_docs = []
    for party_doc in col_party.find({'tags': args.party_tag}):  # tagsのうち、いずれかが一致すれば良い
        policy = RandomPolicy()
        agent_docs.append({
            '_id': ObjectId(),
            'party_id': party_doc['_id'],
            'policy_packed': pack_obj(policy),
            'tags': tags
        })
    col_agent.insert_many(agent_docs)


if __name__ == '__main__':
    main()
