"""
パーティグループにランダム行動エージェントを付与する
"""

import argparse

from pokeai.sim import context
from pokeai.agent import party_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("party_group_tag", help="パーティグループのタグ")
    parser.add_argument("agent_tag", help="エージェントのタグ")
    args = parser.parse_args()
    context.init()
    pg = party_db.load_party_group(args.party_group_tag)
    for party_t in pg:
        agent_info = {"party_id": party_t.party_id,
                      "class_name": "BattleAgentRandom",
                      "observer": {"party_size": len(party_t.poke_sts), "feature_types": []},
                      "agent": {},
                      "tags": [args.agent_tag]}
        party_db.col_agent.insert_one(agent_info)


if __name__ == '__main__':
    main()
