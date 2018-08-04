"""
ランダムなパーティ群とそのレーティングを生成する。
"""

import random
import argparse
from typing import Dict, List, Tuple
import copy
import pickle
import numpy as np
import uuid

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context
from pokeai.agent.util import load_pickle, save_pickle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("n_party", type=int)
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    args = parser.parse_args()
    context.init()
    partygen = PartyGenerator(PartyRule[args.rule])
    parties = [{"party": Party(partygen.generate()), "uuid": str(uuid.uuid4())} for i in range(args.n_party)]
    save_pickle({"parties": parties}, args.dst)


if __name__ == '__main__':
    main()
