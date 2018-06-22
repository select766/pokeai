from typing import TypeVar

from pokeai.sim.move import Move
from pokeai.sim.poke import Poke
import pokeai.sim


class MoveHandlerContext:
    attack_player: int
    attack_poke: Poke
    defend_poke: Poke
    field: TypeVar("pokeai.sim.Field")
    move: Move
    flag: TypeVar("pokeai.sim.PokeDBMoveFlag")
