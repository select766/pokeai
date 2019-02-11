"""
ランダムなパーティ群を生成する。
"""

import argparse

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import context
from pokeai.agent import party_db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n_party", type=int)
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--tag", help="パーティグループのタグ")
    args = parser.parse_args()
    context.init()
    partygen = PartyGenerator(PartyRule[args.rule])
    parties = [partygen.generate() for i in range(args.n_party)]
    group_id = party_db.save_party_group(parties, args.tag)
    print(f"group id: {group_id}")


if __name__ == '__main__':
    main()
