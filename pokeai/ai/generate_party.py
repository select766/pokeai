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
    args = parser.parse_args()
    tags = args.tags.split(",") if args.tags else []
    gen = RandomPartyGenerator()
    parties = [{'_id': ObjectId(), 'party': gen.generate(), 'tags': tags} for _ in range(args.n)]
    col_party.insert_many(parties)


if __name__ == '__main__':
    main()
