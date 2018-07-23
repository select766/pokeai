"""
ゲーム設定のデータベースへのアクセス機能
"""
from typing import List, Callable

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.poke_db_move_flag import PokeDBMoveFlag
from pokeai.sim.poke_db_move_info import PokeDBMoveInfo
from pokeai.sim.poke_param import PokeParam
from pokeai.sim.poke_type import PokeType
from pokeai.sim.poke_param_db import poke_param_db
from pokeai.sim.move_flag_db import move_flag_db
from pokeai.sim.move_info_db import move_info_db, init_move_info_db


class PokeDB:
    def __init__(self):
        init_move_info_db()

    def get_base_stat(self, dexno: Dexno) -> PokeParam:
        return poke_param_db[dexno]

    def get_move_info(self, move: Move) -> PokeDBMoveInfo:
        return move_info_db[move]
