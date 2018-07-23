from typing import List, Dict
from pokeai.sim.move import Move
from pokeai.sim.poke_db_move_info import PokeDBMoveInfo
from pokeai.sim.move_flag_db import move_flag_db
from pokeai.sim.move_group import move_group, MoveGroupName

move_info_db = {}  # type: Dict[Move, PokeDBMoveInfo]


def init_move_info_db():
    # 循環import回避のため最初の利用前に初期化する
    if len(move_info_db) > 0:
        return
    import pokeai.sim.move_handlers as mh
    for m in move_group[MoveGroupName.SIMPLE]:
        move_info_db[m] = PokeDBMoveInfo(move_flag_db[m],
                                         mh.check_hit_attack_default,
                                         mh.launch_move_attack_default,
                                         mh.check_side_effect_none,
                                         mh.launch_side_effect_none)

    move_info_db[Move.SPLASH] = PokeDBMoveInfo(move_flag_db[Move.SPLASH],
                                               mh.check_hit_splash,
                                               mh.launch_move_splash,
                                               mh.check_side_effect_none,
                                               mh.launch_side_effect_none)

    move_info_db[Move.DIG] = PokeDBMoveInfo(move_flag_db[Move.DIG],
                                            mh.check_hit_dig,
                                            mh.launch_move_dig,
                                            mh.check_side_effect_none,
                                            mh.launch_side_effect_none)

    # TODO: ひるみ効果
    move_info_db[Move.BITE] = PokeDBMoveInfo(move_flag_db[Move.BITE],
                                             mh.check_hit_attack_default,
                                             mh.launch_move_attack_default,
                                             mh.check_side_effect_none,
                                             mh.launch_side_effect_none)
