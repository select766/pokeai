from typing import List, Dict, Callable
from pokeai.sim.move import Move
from pokeai.sim.poke import PokeNVCondition
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

    assign(MoveGroupName.QUICKATTACK,
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
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.PARALYSIS))

    assign(MoveGroupName.PARALYSIS_30,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_paralysis(30),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.PARALYSIS))

    assign(MoveGroupName.BODYSLAM,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_paralysis(30, bodyslam=True),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.PARALYSIS))

    assign(MoveGroupName.BURN_10,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_burn(10),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.BURN))

    assign(MoveGroupName.BURN_30,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_burn(30),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.BURN))

    assign(MoveGroupName.POISON_20,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_poison(20),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.POISON))

    assign(MoveGroupName.POISON_40,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_poison(40),
           mh.gen_launch_side_effect_nv_condition(PokeNVCondition.POISON))

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

    assign(MoveGroupName.GLARE,
           mh.gen_check_hit_make_paralysis(False),
           mh.launch_move_make_paralysis,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.THUNDERWAVE,
           mh.gen_check_hit_make_paralysis(True),
           mh.launch_move_make_paralysis,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    # 急所判定の変更はダメージ計算部分に内蔵
    assign(MoveGroupName.CRITICAL,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.EVASION_UP,
           mh.gen_check_hit_change_attacker_rank("evasion", 1),
           mh.gen_launch_move_change_attacker_rank("evasion", 1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.A_UP,
           mh.gen_check_hit_change_attacker_rank("a", 1),
           mh.gen_launch_move_change_attacker_rank("a", 1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.A_UP2,
           mh.gen_check_hit_change_attacker_rank("a", 2),
           mh.gen_launch_move_change_attacker_rank("a", 2),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.B_UP,
           mh.gen_check_hit_change_attacker_rank("b", 1),
           mh.gen_launch_move_change_attacker_rank("b", 1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.B_UP2,
           mh.gen_check_hit_change_attacker_rank("b", 2),
           mh.gen_launch_move_change_attacker_rank("b", 2),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.C_UP,
           mh.gen_check_hit_change_attacker_rank("c", 1),
           mh.gen_launch_move_change_attacker_rank("c", 1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.C_UP2,
           mh.gen_check_hit_change_attacker_rank("c", 2),
           mh.gen_launch_move_change_attacker_rank("c", 2),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.S_UP2,
           mh.gen_check_hit_change_attacker_rank("s", 2),
           mh.gen_launch_move_change_attacker_rank("s", 2),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.ACCURACY_DOWN,
           mh.gen_check_hit_change_defender_rank("accuracy", -1),
           mh.gen_launch_move_change_defender_rank("accuracy", -1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.A_DOWN,
           mh.gen_check_hit_change_defender_rank("a", -1),
           mh.gen_launch_move_change_defender_rank("a", -1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.B_DOWN,
           mh.gen_check_hit_change_defender_rank("b", -1),
           mh.gen_launch_move_change_defender_rank("b", -1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.B_DOWN2,
           mh.gen_check_hit_change_defender_rank("b", -2),
           mh.gen_launch_move_change_defender_rank("b", -2),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.S_DOWN,
           mh.gen_check_hit_change_defender_rank("s", -1),
           mh.gen_launch_move_change_defender_rank("s", -1),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.CONFUSE,
           mh.check_hit_confuse,
           mh.launch_move_confuse,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.SIDE_A_DOWN,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_change_defender_rank("a", -1),
           mh.gen_launch_side_effect_change_defender_rank("a", -1))

    assign(MoveGroupName.SIDE_B_DOWN,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_change_defender_rank("b", -1),
           mh.gen_launch_side_effect_change_defender_rank("b", -1))

    assign(MoveGroupName.SIDE_C_DOWN,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_change_defender_rank("c", -1),
           mh.gen_launch_side_effect_change_defender_rank("c", -1))

    assign(MoveGroupName.SIDE_S_DOWN,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.gen_check_side_effect_change_defender_rank("s", -1),
           mh.gen_launch_side_effect_change_defender_rank("s", -1))

    assign(MoveGroupName.SIDE_CONFUSE,
           mh.check_hit_attack_default,
           mh.launch_move_attack_default,
           mh.check_side_effect_confuse,
           mh.launch_side_effect_confuse)

    assign(MoveGroupName.CONST_20,
           mh.check_hit_attack_default,
           mh.gen_launch_move_const(20),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.CONST_40,
           mh.check_hit_attack_default,
           mh.gen_launch_move_const(40),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.FISSURE,
           mh.check_hit_fissure,
           mh.gen_launch_move_const(65535),
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.EXPLOSION,
           mh.check_hit_explosion,
           mh.launch_move_attack_default,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.LEECHSEED,
           mh.check_hit_leechseed,
           mh.launch_move_leechseed,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.DOUBLEEDGE,
           mh.check_hit_attack_default,
           mh.launch_move_doubleedge,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.ABSORB,
           mh.check_hit_attack_default,
           mh.launch_move_absorb,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.NIGHTSHADE,
           mh.check_hit_nightshade_psywave,
           mh.launch_move_nightshade,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.PSYWAVE,
           mh.check_hit_nightshade_psywave,
           mh.launch_move_psywave,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.RECOVER,
           mh.check_hit_recover,
           mh.launch_move_recover,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.DREAMEATER,
           mh.check_hit_dreameater,
           mh.launch_move_absorb,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.REST,
           mh.check_hit_rest,
           mh.launch_move_rest,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.REFLECT,
           mh.check_hit_reflect,
           mh.launch_move_reflect,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.LIGHTSCREEN,
           mh.check_hit_lightscreen,
           mh.launch_move_lightscreen,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)

    assign(MoveGroupName.THRASH,
           mh.check_hit_thrash,
           mh.launch_move_attack_default,
           mh.check_side_effect_none,
           mh.launch_side_effect_none)
