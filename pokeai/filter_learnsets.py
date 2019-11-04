"""
有効なポケモン・技リストを用いてall_learnsets.jsonをフィルタリング

python3 -m pokeai.filter_learnsets data/dataset/regulations/default/pokemons.json data/dataset/regulations/default/moves.json data/dataset/all_learnsets.json > data/dataset/regulations/default/learnsets.json
"""

import sys
import json
import argparse

from pokeai.util import json_load


def filter_learnsets(valid_pokemons, valid_moves, all_learnsets):
    filtered = {}
    moves_set = set(valid_moves)
    for poke in valid_pokemons:
        fil = list(set(all_learnsets[poke]) & moves_set)
        fil.sort()
        filtered[poke] = fil
    return filtered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("valid_pokemons")
    parser.add_argument("valid_moves")
    parser.add_argument("all_learnsets")
    args = parser.parse_args()
    result = filter_learnsets(json_load(args.valid_pokemons),
                              json_load(args.valid_moves),
                              json_load(args.all_learnsets))
    sys.stdout.write(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
