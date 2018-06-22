from typing import List, Optional

from pokeai.sim.poke import Poke
from pokeai.sim.poke_static import PokeStatic


class Party:
    """
    パーティを表す。対戦の動的な状態を含む。
    """
    pokes: List[Poke]
    fighting_idx: int

    def __init__(self, poke_sts: List[PokeStatic]):
        self.pokes = [Poke(st) for st in poke_sts]
        self.fighting_idx = 0

    def get(self, idx: Optional[int] = None):
        if idx is None:
            idx = self.fighting_idx
        return self.pokes[idx]
