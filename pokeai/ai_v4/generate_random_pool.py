"""
強さ測定の基準となるランダムなパーティ群を生成する。

python -m pokeai.ai_v4.generate_random_pool out 100

"""
import copy
from typing import List
import pickle
import argparse
import numpy as np
from tqdm import tqdm

from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from . import pokeai_env
from . import party_generation_helper
from . import util
from .random_rating import generate_random_parties

logger = util.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("n_parties", type=int)
    parser.add_argument("--party_size", type=int, default=3)
    args = parser.parse_args()
    parties = generate_random_parties(args.party_size, args.n_parties)
    with open(args.out, "wb") as f:
        pickle.dump(parties, f)


if __name__ == '__main__':
    main()
