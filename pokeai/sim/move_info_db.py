from typing import List, Dict, Callable
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

    def assign(group: MoveGroupName,
               check_hit: Callable, launch_move: Callable, check_side_effect: Callable, launch_side_effect: Callable):
        for m in move_group[group]:
            move_info_db[m] = PokeDBMoveInfo(move_flag_db[m],
                                             check_hit,
                                             launch_move,
                                             check_side_effect,
                                             launch_side_effect)

    assign(MoveGroupName.SIMPLE,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.SWIFT,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.SPLASH,
           mh.check_hit_splash,
           mh.launch_move_splash,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.HYPERBEAM,
           mh.check_hit_attack_default,
           mh.launch_move_hyperbeam,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.FLINCH_10,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_ratio(10),
           mh.launch_side_effect_flinch)

    assign(MoveGroupName.FLINCH_30,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_ratio(30),
           mh.launch_side_effect_flinch)

    assign(MoveGroupName.DIG,
           mh.check_hit_dig,
           mh.launch_move_dig,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.BLIZZARD,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_freeze(30),
           mh.launch_side_effect_freeze)

    assign(MoveGroupName.FREEZE_10,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_freeze(10),
           mh.launch_side_effect_freeze)

    assign(MoveGroupName.PARALYSIS_10,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_paralysis(10),
           mh.launch_side_effect_paralysis)

    assign(MoveGroupName.PARALYSIS_30,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_paralysis(30),
           mh.launch_side_effect_paralysis)

    assign(MoveGroupName.BODYSLAM,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_paralysis(30, bodyslam=True),
           mh.launch_side_effect_paralysis)

    assign(MoveGroupName.BURN_10,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_burn(10),
           mh.launch_side_effect_burn)

    assign(MoveGroupName.BURN_30,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_burn(30),
           mh.launch_side_effect_burn)

    assign(MoveGroupName.POISON_20,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_poison(20),
           mh.launch_side_effect_poison)

    assign(MoveGroupName.POISON_40,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_poison(40),
           mh.launch_side_effect_poison)

    assign(MoveGroupName.HYPNOSIS,
           mh.check_hit_hypnosis,
           mh.launch_move_hypnosis,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.TOXIC,
           mh.check_hit_make_poison,
           mh.gen_launch_move_make_poison(True),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.POISONGAS,
           mh.check_hit_make_poison,
           mh.gen_launch_move_make_poison(False),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)
