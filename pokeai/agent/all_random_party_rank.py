"""
ランダムパーティ・ランダム方策での強さランキング
ポケモン複数体を1パーティに入れる。
覚えられる技制約有効。
"""

import random
from typing import Dict, List, Tuple
import copy
import numpy as np

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

learnable_moves_db = {}  # type: Dict[Dexno, List[Move]]


def init_party_generator():
    # 実装済み技の列挙
    implemented_moves = set(move_info_db.keys())
    # ポケモンごとに覚えられる技を列挙
    for dexno, mlcs in move_learn_db.items():
        # レベルと技マシンで同じ技を覚える場合があるため、いったんsetにしてからlist
        moves = list({mlc.move for mlc in mlcs if mlc.move in implemented_moves})
        learnable_moves_db[dexno] = moves


def generate_random_party() -> Party:
    """
    ランダムなパーティを生成する。
    :return:
    """
    pokes = []
    dexnos = []
    while len(pokes) < 3:
        dexno = random.choice(list(Dexno))
        if dexno in dexnos:
            # 同じポケモンを複数入れない
            continue
        learnable_moves = learnable_moves_db[dexno]
        if len(learnable_moves) == 0:
            continue
        moves = random.sample(learnable_moves, min(4, len(learnable_moves)))
        poke = PokeStatic.create(dexno, moves)
        dexnos.append(dexno)
        pokes.append(poke)
    return Party(pokes)


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


def league(parties: List[Party]) -> List[int]:
    win_count = [0] * len(parties)
    for i in range(len(parties)):
        for j in range(i + 1, len(parties)):
            winner = match((parties[i], parties[j]))
            if winner >= 0:
                win_count[[i, j][winner]] += 1
    return win_count


def display_result(parties: List[Party], win_count: List[int]):
    order = np.argsort(win_count)
    for p in order:
        print(f"win: {win_count[p]}")
        print(parties[p])


def main():
    context.init()
    init_party_generator()
    parties = [generate_random_party() for i in range(100)]
    win_count = league(parties)
    display_result(parties, win_count)


if __name__ == '__main__':
    main()
