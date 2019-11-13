"""
パーティ群のランダム生成
"""

import argparse

from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.util import pickle_dump


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("-n", type=int, default=100)
    args = parser.parse_args()
    gen = RandomPartyGenerator()
    parties = [gen.generate() for _ in range(args.n)]
    pickle_dump(parties, args.dst)


if __name__ == '__main__':
    main()
