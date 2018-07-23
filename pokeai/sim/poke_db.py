"""
ゲーム設定のデータベースへのアクセス機能
"""
from typing import List, Callable

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.poke_db_move_flag import PokeDBMoveFlag
from pokeai.sim.poke_param import PokeParam
from pokeai.sim.poke_type import PokeType
from pokeai.sim.poke_param_db import poke_param_db
from pokeai.sim.move_flag_db import move_flag_db


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

    def get_base_stat(self, dexno: Dexno) -> PokeParam:
        return poke_param_db[dexno]

    def get_move_info(self, move: Move) -> PokeDBMoveInfo:
        import pokeai.sim.move_handlers as mh
        if move == Move.BITE:
            return PokeDBMoveInfo(move_flag_db[move],
                                  mh.check_hit_attack_default,
                                  mh.launch_move_attack_default,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        if move == Move.VINEWHIP:
            return PokeDBMoveInfo(move_flag_db[move],
                                  mh.check_hit_attack_default,
                                  mh.launch_move_attack_default,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        if move == Move.SPLASH:
            return PokeDBMoveInfo(move_flag_db[move],
                                  mh.check_hit_splash,
                                  mh.launch_move_splash,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        if move == Move.DIG:
            return PokeDBMoveInfo(move_flag_db[move],
                                  mh.check_hit_dig,
                                  mh.launch_move_dig,
                                  mh.check_side_effect_none,
                                  mh.launch_side_effect_none)
        raise NotImplementedError
