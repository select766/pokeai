"""
山登り法のハイパラ調整のため、ランダムなパラメータで山登り法を呼び出しパーティ群を生成する。
"""

import subprocess

import random
import argparse
from typing import Dict, List, Tuple, Iterable, Optional
import copy
import os
import pickle
import numpy as np
import uuid
from tqdm import tqdm
from multiprocessing import Pool

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.move_info_db import move_info_db
from pokeai.sim.move_learn_db import move_learn_db
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context
from pokeai.agent.common import match_random_policy
from pokeai.agent.util import load_pickle, save_pickle, reset_random, load_party_rate, load_yaml, save_yaml


def run_random(args, dst_dir):
    # 各種ランダム設定
    neighbor = random.choice([5, 10, 20])
    iter_ = random.choice([1, 3, 10, 30, 100])
    neighbor_move_remove_rate = random.uniform(0.01, 0.5)
    neighbor_move_add_rate = random.uniform(0.01, 0.5)
    rule_params_file = os.path.join(dst_dir, "rule_params.yaml")
    save_yaml({"neighbor_move_remove_rate": neighbor_move_remove_rate,
               "neighbor_move_add_rate": neighbor_move_add_rate}, rule_params_file)
    all_params = {"neighbor": neighbor, "iter": iter_,
                  "neighbor_move_remove_rate": neighbor_move_remove_rate,
                  "neighbor_move_add_rate": neighbor_move_add_rate}
    save_yaml(all_params, os.path.join(dst_dir, "all_params.yaml"))
    print(all_params)
    call_args = ["python", "-m", "pokeai.agent.hill_climbing",
                 os.path.join(dst_dir, 'parties.bin'),
                 args.seed_party, args.baseline_party_pool, args.baseline_party_rate,
                 "--rule_params", rule_params_file,
                 "--neighbor", str(neighbor),
                 "--iter", str(iter_)]
    if args.j:
        call_args.extend(["-j", str(args.j)])
    subprocess.check_call(call_args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst_dir")
    parser.add_argument("n_group", type=int)
    parser.add_argument("seed_party", help="更新元になるパーティ群")
    parser.add_argument("baseline_party_pool", help="レーティング測定相手パーティ群")
    parser.add_argument("baseline_party_rate", help="レーティング測定相手パーティ群のレーティング")
    parser.add_argument("-j", type=int, help="並列処理数")
    args = parser.parse_args()
    context.init()

    for i in range(args.n_group):
        run_uuid = str(uuid.uuid4())
        run_dst_dir = os.path.join(args.dst_dir, run_uuid)
        os.makedirs(run_dst_dir)
        run_random(args, run_dst_dir)


if __name__ == '__main__':
    main()
