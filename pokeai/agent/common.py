import random
from typing import Dict, List, Tuple
import copy

from pokeai.agent.battle_agent import BattleAgent
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


def match_agents(battle_agents: List[BattleAgent], logger=None) -> int:
    """
    エージェント同士を対戦させる。
    :param battle_agents:
    :return: 勝ったプレイヤー。引き分けは-1。
    """
    field = Field([battle_agents[0].party_t.create(), battle_agents[1].party_t.create()])
    field.rng = GameRNGRandom()
    field.rng.set_field(field)
    field.put_record = logger or (lambda record: None)

    winner = -1
    next_phase = FieldPhase.BEGIN
    while True:
        actions = []
        for p in range(2):
            actions.append(battle_agents[p].get_action(field, p, logger=logger))
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
