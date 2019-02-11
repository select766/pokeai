from typing import List, Optional
from bson import ObjectId

from pokeai.sim.poke import Poke
from pokeai.sim.poke_static import PokeStatic


class Party:
    """
    パーティを表す。対戦の動的な状態を含む。
    """
    pokes: List[Poke]
    fighting_idx: int
    party_id: ObjectId

    def __init__(self, poke_sts: List[PokeStatic], party_id: Optional[ObjectId] = None):
        self.pokes = [Poke(st) for st in poke_sts]
        self.fighting_idx = 0
        self.party_id = party_id

    def get(self, idx: Optional[int] = None):
        if idx is None:
            idx = self.fighting_idx
        return self.pokes[idx]

    def __str__(self):
        s = ""
        if self.party_id is not None:
            s += str(self.party_id) + "\n"
        for i, poke in enumerate(self.pokes):
            if i == self.fighting_idx:
                s += "* "
            else:
                s += "  "
            s += str(poke)
            s += "\n"
        return s
