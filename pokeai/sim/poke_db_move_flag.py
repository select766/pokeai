from typing import Dict

from pokeai.sim.poke_type import PokeType


class PokeDBMoveFlag:
    """
    技のパラメータ
    """
    move_type: PokeType
    power: int
    accuracy: int
    pp: int
    names: Dict[str, str]  # "ja" -> japanese name, "en" -> english name

    def __init__(self, move_type: PokeType, power: int, accuracy: int, pp: int, names: Dict[str, str]):
        self.move_type = move_type
        self.power = power
        self.accuracy = accuracy
        self.pp = pp
        self.names = names
