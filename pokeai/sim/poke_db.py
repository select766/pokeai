"""
ゲーム設定のデータベースへのアクセス機能
"""
from typing import List, Callable

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.poke_type import PokeType


class PokeDBBaseStat:
    h: int
    a: int
    b: int
    c: int
    s: int
    poke_types: List[PokeType]

    def __init__(self, h: int, a: int, b: int, c: int, s: int, poke_types: List[PokeType]):
        self.h = h
        self.a = a
        self.b = b
        self.c = c
        self.s = s
        self.poke_types = poke_types


class PokeDBMoveFlag:
    """
    技のパラメータ
    """
    move_type: PokeType
    power: int
    accuracy: int  # 命中率、0は必中
    pp: int

    def __init__(self, move_type: PokeType, power: int, accuracy: int, pp: int):
        self.move_type = move_type
        self.power = power
        self.accuracy = accuracy
        self.pp = pp


class PokeDBMoveInfo:
    """
    技のパラメータおよび判定処理
    """
    flag: PokeDBMoveFlag
    check_hit: Callable
    launch_move: Callable
    check_side_effect: Callable
    launch_side_effect: Callable

    def __init__(self, flag: PokeDBMoveFlag,
                 check_hit: Callable,
                 launch_move: Callable,
                 check_side_effect: Callable,
                 launch_side_effect: Callable,
                 ):
        self.flag = flag
        self.check_hit = check_hit
        self.launch_move = launch_move
        self.check_side_effect = check_side_effect
        self.launch_side_effect = launch_side_effect


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

    def get_move_info(self, move: Move) -> PokeDBMoveInfo:
        import pokeai.sim.move_handlers as mh
        if move == Move.BITE:
            return PokeDBMoveInfo(PokeDBMoveFlag(PokeType.NORMAL, 60, 100, 20),
                                  mh.check_hit_attack_default,
                                  mh.launch_move_attack_default,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        if move == Move.SPLASH:
            return PokeDBMoveInfo(PokeDBMoveFlag(PokeType.NORMAL, 0, 0, 40),
                                  mh.check_hit_splash,
                                  mh.launch_move_splash,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        raise NotImplementedError
