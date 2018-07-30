"""
ランダムなパーティ群とそのレーティングを生成する。
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


def rating_battle(parties: List[Party], match_count: int) -> List[float]:
    """
    パーティ同士を多数戦わせ、レーティングを算出する。
    :param parties:
    :param match_count:
    :return: パーティのレーティング
    """
    assert len(parties) % 2 == 0
    rates = np.full((len(parties),), 1500.0)
    for i in range(match_count):
        # 対戦相手を決める
        rates_with_random = rates + np.random.normal(scale=200., size=rates.shape)
        ranking = np.argsort(rates_with_random)
        for j in range(0, len(parties), 2):
            left = ranking[j]
            right = ranking[j + 1]
            winner = match((parties[left], parties[right]))
            # レートを変動させる
            if winner >= 0:
                left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0))
                if winner == 0:
                    left_incr = 32 * (1.0 - left_winrate)
                else:
                    left_incr = 32 * (-left_winrate)
                rates[left] += left_incr
                rates[right] -= left_incr
        abs_mean_diff = np.mean(np.abs(rates - 1500.0))
        print(f"{i} rate mean diff: {abs_mean_diff}")
    return rates.tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party", type=int)
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    args = parser.parse_args()
    context.init()
    partygen = PartyGenerator(PartyRule[args.rule])
    parties = [Party(partygen.generate()) for i in range(args.party)]
    rates = rating_battle(parties, args.match_count)
    with open(args.dst, "wb") as f:
        pickle.dump({"parties": parties, "rates": rates}, f)


if __name__ == '__main__':
    main()
