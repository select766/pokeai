"""
ランダムパーティ・ランダム方策での強さランキング
パーティと対戦結果を保存する。
"""

import random
import argparse
from typing import Dict, List, Tuple
import copy
import pickle
import numpy as np
from tqdm import tqdm

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


def match(parties: Tuple[Party, Party]) -> int:
    field = Field([copy.deepcopy(parties[0]), copy.deepcopy(parties[1])])
    field.rng = GameRNGRandom()
    field.rng.set_field(field)
    field.put_record = lambda record: None

    winner = -1
    next_phase = FieldPhase.BEGIN
    while True:
        actions = []
        for p in range(2):
            legals = field.get_legal_actions(p)
            if len(legals) == 0:
                actions.append(None)
            else:
                actions.append(random.choice(legals))
        if next_phase is FieldPhase.BEGIN:
            field.actions_begin = actions
        elif next_phase is FieldPhase.FAINT_CHANGE:
            field.actions_faint_change = actions
        next_phase = field.step()
        if next_phase is FieldPhase.GAME_END:
            winner = field.winner
            break
        if field.turn_number >= 64:
            break
    return winner


def league(parties: List[Party], match_count: int) -> List[Tuple[int, int, int]]:
    """
    パーティ同士を多数戦わせる
    :param parties:
    :param match_count:
    :return: Tuple[パーティインデックス0、パーティインデックス1、勝敗(0or1or-1=引き分け)
    """
    results = []
    for i in tqdm(range(len(parties))):
        js = list(range(len(parties)))
        js.remove(i)
        random.shuffle(js)
        for j in js[:match_count]:
            winner = match((parties[i], parties[j]))
            results.append((i, j, winner))
    return results


# def display_result(parties: List[Party], win_count: List[int]):
#     order = np.argsort(win_count)
#     for p in order:
#         print(f"win: {win_count[p]}")
#         print(parties[p])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party", type=int)
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--match_count", type=int, default=0, help="1パーティあたりの対戦回数")
    args = parser.parse_args()
    context.init()
    partygen = PartyGenerator(PartyRule[args.rule])
    parties = [Party(partygen.generate()) for i in range(args.party)]
    match_results = league(parties, args.match_count or (args.party - 1))
    with open(args.dst, "wb") as f:
        pickle.dump({"parties": parties, "match_results": match_results}, f)


if __name__ == '__main__':
    main()
