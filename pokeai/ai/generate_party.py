"""
パーティ群のランダム生成
指定したタグをつけてDBに格納する
"""

import argparse
import random
from bson import ObjectId

from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.ai.party_db import col_party


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tags")
    parser.add_argument("-n", type=int, default=100)
    parser.add_argument("--all_pokemon_once", action="store_true",
                        help="全ポケモンをパーティ先頭のポケモンに1回ずつ用いる。控えのポケモンはランダム。'-n'は無視。")
    parser.add_argument("-r", default="default", help="regulation")
    args = parser.parse_args()
    tags = args.tags.split(",") if args.tags else []
    gen = RandomPartyGenerator(regulation=args.r)
    if args.all_pokemon_once:
        parties = []
        for first_poke in gen._pokemons:
            while True:
                fix_species = [first_poke]
                while len(fix_species) < len(gen._regulation["levels"]):
                    cand_poke = random.choice(gen._pokemons)
                    if cand_poke not in fix_species:
                        fix_species.append(cand_poke)
                try:
                    party = gen.generate(fix_species=fix_species)
                    parties.append({'_id': ObjectId(), 'party': party, 'tags': tags})
                    break
                except ValueError:
                    # 制約条件を満たせなかった場合（LV55でしか存在しないポケモンが複数いる場合）
                    continue
    else:
        parties = [{'_id': ObjectId(), 'party': gen.generate(), 'tags': tags} for _ in range(args.n)]
    col_party.insert_many(parties)


if __name__ == '__main__':
    main()
