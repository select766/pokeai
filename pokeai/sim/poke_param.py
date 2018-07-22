from typing import Dict, List

from pokeai.sim.poke_type import PokeType


class PokeParam:
    dexno: int
    h: int
    a: int
    b: int
    c: int
    s: int
    types: List[PokeType]
    names: Dict[str, str]  # "ja" -> japanese name, "en" -> english name

    def __init__(self, dexno: int, h: int, a: int, b: int, c: int, s: int, types: List[PokeType],
                 names: Dict[str, str]):
        self.dexno = dexno
        self.h = h
        self.a = a
        self.b = b
        self.c = c
        self.s = s
        self.types = types
        self.names = names
