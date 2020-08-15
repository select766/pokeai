"""
パーティ群のランダム生成
指定したタグをつけてDBに格納する
"""

import argparse
from bson import ObjectId

from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.ai.party_db import col_party


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tags")
    parser.add_argument("-n", type=int, default=100)
    parser.add_argument("--all_pokemon_once", action="store_true")
    parser.add_argument("-r", default="default", help="regulation")
    args = parser.parse_args()
    tags = args.tags.split(",") if args.tags else []
    gen = RandomPartyGenerator(regulation=args.r)
    if args.all_pokemon_once:
        assert len(gen._regulation["levels"]) == 1, "パーティのポケモン1体のみ対応"
        parties = [{'_id': ObjectId(), 'party': gen.generate(fix_species=[poke]), 'tags': tags} for poke in
                   gen._learnsets.keys()]
    else:
        parties = [{'_id': ObjectId(), 'party': gen.generate(), 'tags': tags} for _ in range(args.n)]
    col_party.insert_many(parties)


if __name__ == '__main__':
    main()
