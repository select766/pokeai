from typing import List, Optional
from bson import ObjectId
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic


class PartyTemplate:
    """
    パーティ構成を表す。戦闘中の状態は持たない。
    """
    poke_sts: List[PokeStatic]
    party_id: ObjectId

    def __init__(self, poke_sts: List[PokeStatic], party_id: Optional[ObjectId] = None):
        self.poke_sts = poke_sts
        self.party_id = party_id or ObjectId()  # ランダム生成

    def create(self) -> Party:
        """
        戦闘中の状態を持つPartyインスタンスを生成する
        :return:
        """
        return Party(self.poke_sts, self.party_id)

    def __str__(self):
        s = ""
        if self.party_id is not None:
            s += str(self.party_id) + "\n"
        for i, poke_st in enumerate(self.poke_sts):
            s += str(poke_st)
            s += "\n"
        return s
