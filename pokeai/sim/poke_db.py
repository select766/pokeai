"""
ゲーム設定のデータベースへのアクセス機能
"""
from pokeai.sim.dexno import Dexno
from pokeai.sim.poke_type import PokeType


class PokeDB:
    def __init__(self):
        pass

    def get_base_stat(self, dexno: Dexno) -> dict:
        # TODO: ファイルから読む
        if dexno == Dexno.BULBASAUR:
            return {"h": 45, "a": 49, "b": 49, "c": 65, "s": 45, "types": [PokeType.GRASS, PokeType.POISON]}
        if dexno == Dexno.IVYSAUR:
            return {"h": 60, "a": 62, "b": 63, "c": 63, "s": 80, "types": [PokeType.GRASS, PokeType.POISON]}
        if dexno == Dexno.VENUSAUR:
            return {"h": 80, "a": 82, "b": 83, "c": 100, "s": 80, "types": [PokeType.GRASS, PokeType.POISON]}
        if dexno == Dexno.CHARMANDER:
            return {"h": 39, "a": 52, "b": 43, "c": 50, "s": 65, "types": [PokeType.FIRE]}
        if dexno == Dexno.CHARMELEON:
            return {"h": 58, "a": 64, "b": 58, "c": 65, "s": 80, "types": [PokeType.FIRE]}
        if dexno == Dexno.CHARIZARD:
            return {"h": 78, "a": 84, "b": 78, "c": 85, "s": 100, "types": [PokeType.FIRE, PokeType.FLYING]}
        raise NotImplementedError
