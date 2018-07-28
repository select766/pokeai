from typing import List, Tuple, Callable

from pokeai.sim.game_rng import GameRNGReason
from pokeai.sim.move import Move
from pokeai.sim.move_handler_context import MoveHandlerContext
from pokeai.sim.multi_turn_move_info import MultiTurnMoveInfo
from pokeai.sim.poke import Poke, PokeNVCondition
from pokeai.sim.poke_type import PokeType


def _check_hit_by_accuracy(context: MoveHandlerContext) -> bool:
    """
    命中率による判定を行う
    :param context:
    :return:
    """
    # 命中率による判定
    # https://wiki.xn--rckteqa2e.com/wiki/%E5%91%BD%E4%B8%AD
    if context.flag.accuracy > 0:
        # 技の命中率×自分のランク補正(命中率)÷相手のランク補正(回避率)
        hit_ratio_table = {100: 255, 95: 242, 90: 229, 85: 216,
                           80: 204, 75: 191, 70: 178, 65: 165, 60: 152, 55: 140, 50: 127, 30: 76, 0: 0}
        hit_ratio = hit_ratio_table[context.flag.accuracy]
        hit_ratio = hit_ratio * 2 // (-context.attack_poke.rank_accuracy.value + 2)
        hit_ratio = hit_ratio * 2 // (context.defend_poke.rank_evasion.value + 2)
        # 1~255の乱数と比較
        hit_judge_rnd = context.field.rng.gen(context.attack_player, GameRNGReason.HIT, 254) + 1
        if hit_ratio <= hit_judge_rnd:
            context.field.put_record_other("命中率による判定で外れた")
            return False
    else:
        # 必中技
        pass
    return True


def _check_hit_by_avoidance(context: MoveHandlerContext) -> bool:
    """
    命中率、あなをほる状態による判定
    :param context:
    :return:
    """
    if context.defend_poke.v_dig:
        context.field.put_record_other("あなをほる状態で外れた")
        return False

    return _check_hit_by_accuracy(context)


def _check_hit_by_type_match(context: MoveHandlerContext) -> bool:
    """
    タイプ相性で無効でないことを判定
    :param context:
    :return:
    """

    move_type = context.flag.move_type
    type_matches_x2 = PokeType.get_match_list(move_type, context.defend_poke.poke_types)
    type_matches_prod = type_matches_x2[0] * (type_matches_x2[1] if len(type_matches_x2) == 2 else 2)
    return type_matches_prod != 0


def check_hit_attack_default(context: MoveHandlerContext) -> bool:
    """
    攻撃技のデフォルト命中判定
    相性、命中率、あなをほる状態による判定
    :param context:
    :return:
    """
    if not _check_hit_by_type_match(context):
        return False
    if not _check_hit_by_avoidance(context):
        return False

    return True


def check_hit_nightshade_psywave(context: MoveHandlerContext) -> bool:
    """
    ナイトヘッド・サイコウェーブ命中判定
    相性無視
    命中率、あなをほる状態による判定
    :param context:
    :return:
    """
    if not _check_hit_by_avoidance(context):
        return False

    return True


def calc_damage_core(power: int, attack_level: int, attack: int, defense: int,
                     critical: bool, same_type: bool, type_matches_x2: List[int],
                     rnd: int):
    """
    ダメージ計算のコア。
    :param power: 威力
    :param attack_level: 攻撃側レベル(急所考慮なし)
    :param attack: 攻撃側こうげき/とくしゅ(急所考慮あり)
    :param defense: 防御側ぼうぎょ/とくしゅ(急所考慮あり)
    :param critical: 急所
    :param same_type: タイプ一致
    :param type_matches_x2: 技と防御側相性(タイプごとに、相性補正の2倍の値を与える: 等倍なら2、半減なら1)
    :param rnd: 0~38の乱数
    :return:
    """
    assert 0 <= rnd <= 38
    if critical:
        attack_level *= 2
    damage = attack_level * 2 // 5 + 2
    damage = damage * power * attack // defense // 50 + 2
    if same_type:
        damage = damage * 3 // 2
    for tmx2 in type_matches_x2:
        damage = damage * tmx2 // 2
    damage = damage * (rnd + 217) // 255
    return damage


def calc_damage(context: MoveHandlerContext) -> Tuple[int, bool]:
    """
    通常攻撃技のダメージ計算を行う。
    ダメージ量と、相手が瀕死になるかどうか
    """
    power = context.flag.power  # 威力
    attack_level = context.attack_poke.lv  # 攻撃側レベル

    # 急所判定
    critical_ratio = context.attack_poke.base_s // 2
    if context.move in [Move.CRABHAMMER, Move.KARATECHOP, Move.RAZORLEAF, Move.SLASH]:
        # 急所に当たりやすい技
        critical_ratio *= 8
    if critical_ratio > 255:
        critical_ratio = 255
    critical = context.field.rng.gen(context.attack_player, GameRNGReason.CRITICAL, 255) + 1 < critical_ratio
    if critical:
        context.field.put_record_other("きゅうしょにあたった")
    # タイプ処理
    move_type = context.flag.move_type
    same_type = move_type in context.attack_poke.poke_types
    type_matches_x2 = PokeType.get_match_list(move_type, context.defend_poke.poke_types)
    type_matches_prod = type_matches_x2[0] * (type_matches_x2[1] if len(type_matches_x2) == 2 else 2)
    if type_matches_prod > 4:
        context.field.put_record_other("こうかはばつぐんだ")
    elif type_matches_prod == 0:
        context.field.put_record_other("こうかはないようだ")
        # 命中判定時点で本来外れているので、ダメージ計算はしないはず
        raise RuntimeError
    elif type_matches_prod < 4:
        context.field.put_record_other("こうかはいまひとつのようだ")

    if PokeType.is_physical(move_type):
        attack = context.attack_poke.eff_a(critical)
        defense = context.defend_poke.eff_b(critical)
        if context.defend_poke.v_reflect:
            # 急所にかかわらず効果あり
            attack //= 4
            defense //= 2
    else:
        attack = context.attack_poke.eff_c(critical)
        defense = context.defend_poke.eff_c(critical)
        if context.defend_poke.v_lightscreen:
            attack //= 4
            defense //= 2
    if context.move in [Move.EXPLOSION, Move.SELFDESTRUCT]:
        defense = defense // 2  # 自爆技は防御を半分にして計算(TODO: 混乱ダメージも倍になるが未実装)
    damage_rnd = context.field.rng.gen(context.attack_player, GameRNGReason.DAMAGE, 38)
    damage = calc_damage_core(power=power,
                              attack_level=attack_level,
                              attack=attack, defense=defense,
                              critical=critical, same_type=same_type,
                              type_matches_x2=type_matches_x2, rnd=damage_rnd)
    make_faint = False
    if damage >= context.defend_poke.hp:
        # ダメージは受け側のHP以下
        damage = context.defend_poke.hp
        make_faint = True
    return damage, make_faint


def launch_move_attack_default(context: MoveHandlerContext):
    """
    攻撃技のデフォルト発動
    :param context:
    :return:
    """
    # 威力・相性に従ってダメージ計算し、受け手のHPから減算
    damage, make_faint = calc_damage(context)
    context.field.put_record_other(f"ダメージ: {damage}")
    context.defend_poke.hp_incr(-damage)


def launch_move_doubleedge(context: MoveHandlerContext):
    """
    すてみタックル等反動技
    :param context:
    :return:
    """
    # 威力・相性に従ってダメージ計算し、受け手のHPから減算
    damage, make_faint = calc_damage(context)
    context.field.put_record_other(f"ダメージ: {damage}")
    context.defend_poke.hp_incr(-damage)
    selfdamage = damage // 4
    if selfdamage >= context.attack_poke.hp:
        selfdamage = context.attack_poke.hp
    context.field.put_record_other(f"反動ダメージ: {selfdamage}")
    context.attack_poke.hp_incr(-selfdamage)


def launch_move_absorb(context: MoveHandlerContext):
    """
    すいとる等吸収技
    ゆめくいも同様
    :param context:
    :return:
    """
    # 威力・相性に従ってダメージ計算し、受け手のHPから減算
    damage, make_faint = calc_damage(context)
    context.field.put_record_other(f"ダメージ: {damage}")
    context.defend_poke.hp_incr(-damage)
    max_recover = context.attack_poke.max_hp - context.attack_poke.hp
    recover = min(max_recover, damage // 2)
    context.field.put_record_other(f"吸収ダメージ: {recover}")
    context.attack_poke.hp_incr(recover)


def check_hit_fissure(context: MoveHandlerContext):
    """
    一撃必殺の命中判定
    :param context:
    :return:
    """
    # 素早さが攻撃側<防御側 なら当たらない
    if context.attack_poke.eff_s() < context.defend_poke.eff_s():
        context.field.put_record_other(f"ぜんぜんきいてない")
        return False
    # そのほかは通常技と同じ
    return check_hit_attack_default(context)


def check_hit_explosion(context: MoveHandlerContext):
    """
    自爆技の命中判定
    命中にかかわらず、攻撃側の体力を0にする
    :param context:
    :return:
    """
    context.attack_poke.hp_incr(-context.attack_poke.hp)
    return check_hit_attack_default(context)


def gen_launch_move_const(damage: int):
    """
    固定ダメージ技
    :param damage: ダメージ量(一撃必殺は65535)
    :return:
    """

    def launch_move_const(context: MoveHandlerContext):
        cur_damage = damage
        if cur_damage >= context.defend_poke.hp:
            cur_damage = context.defend_poke.hp
        context.field.put_record_other(f"固定ダメージ: {cur_damage}")
        context.defend_poke.hp_incr(-cur_damage)

    return launch_move_const


def launch_move_nightshade(context: MoveHandlerContext):
    """
    レベルと同じ数の固定ダメージ
    :param context:
    :return:
    """
    cur_damage = context.attack_poke.lv
    if cur_damage >= context.defend_poke.hp:
        cur_damage = context.defend_poke.hp
    context.field.put_record_other(f"固定ダメージ: {cur_damage}")
    context.defend_poke.hp_incr(-cur_damage)


def launch_move_psywave(context: MoveHandlerContext):
    """
    1~レベル*1.5-1のダメージ
    :param context:
    :return:
    """
    cur_damage = context.field.rng.gen(context.attack_player, GameRNGReason.PSYWAVE,
                                       context.attack_poke.lv * 3 // 2 - 1)
    if cur_damage >= context.defend_poke.hp:
        cur_damage = context.defend_poke.hp
    context.field.put_record_other(f"レベル比例ダメージ: {cur_damage}")
    context.defend_poke.hp_incr(-cur_damage)


def check_hit_splash(context: MoveHandlerContext) -> bool:
    """
    はねる
    :param context:
    :return:
    """
    return True


def launch_move_splash(context: MoveHandlerContext):
    """
    はねる
    :param context:
    :return:
    """
    context.field.put_record_other("なにもおこらない")


def check_hit_dig(context: MoveHandlerContext) -> bool:
    """
    あなをほる(連続技)
    1ターン目: 必ず成功
    2ターン目: あなをほる状態解除、普通の命中判定
    :param context:
    :return:
    """

    # TODO: どのタイミングでmulti_turn_move_infoを解除するのかよく考えるべき
    # 外れる場合を考えるとここで解除することになるが、そうするとlaunch_move_digに情報を伝えられない
    def abort_dig(poke: Poke):
        poke.v_dig = False

    if context.attack_poke.multi_turn_move_info is None:
        # 1ターン目
        context.attack_poke.multi_turn_move_info = MultiTurnMoveInfo(context.move, abort_dig)
        return True
    else:
        # 2ターン目
        context.attack_poke.multi_turn_move_info = None
        context.attack_poke.v_dig = False
        return check_hit_attack_default(context)


def launch_move_dig(context: MoveHandlerContext):
    """
    あなをほる
    :param context:
    :return:
    """
    if context.attack_poke.multi_turn_move_info is not None:
        # 1ターン目
        context.attack_poke.v_dig = True
        context.field.put_record_other("ちちゅうにもぐった")
    else:
        # 2ターン目
        launch_move_attack_default(context)


def launch_move_hyperbeam(context: MoveHandlerContext):
    """
    はかいこうせん
    :param context:
    :return:
    """
    # 威力・相性に従ってダメージ計算し、受け手のHPから減算
    damage, make_faint = calc_damage(context)
    context.field.put_record_other(f"ダメージ: {damage}")
    context.defend_poke.hp_incr(-damage)
    if not make_faint:
        # 倒していない場合、反動状態になる
        context.field.put_record_other(f"はかいこうせんの反動状態付与")
        context.attack_poke.v_hyperbeam = True


def check_side_effect_none(context: MoveHandlerContext) -> bool:
    """
    追加効果なし
    :param context:
    :return:
    """
    return False


def gen_check_side_effect_ratio(side_effect_ratio: int) -> Callable[[MoveHandlerContext], bool]:
    """
    特定確率で必ず追加効果がある技のハンドラ生成
    :param side_effect_ratio: 追加効果確率
    :return:
    """

    def check_side_effect_ratio(context: MoveHandlerContext):
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
        return r < side_effect_ratio

    return check_side_effect_ratio


def launch_side_effect_none(context: MoveHandlerContext):
    """
    追加効果なし
    :param context:
    :return:
    """
    return


def launch_side_effect_flinch(context: MoveHandlerContext):
    """
    ひるみ
    :param context:
    :return:
    """
    context.field.put_record_other(f"追加効果: ひるみ")
    context.defend_poke.v_flinch = True
    return


def gen_check_side_effect_freeze(side_effect_ratio: int) -> Callable[[MoveHandlerContext], bool]:
    """
    追加効果で凍らせる技のハンドラ生成
    :param side_effect_ratio: 追加効果確率
    :return:
    """

    def check_side_effect_ratio(context: MoveHandlerContext):
        if PokeType.ICE in context.defend_poke.poke_types:
            # こおりタイプは凍らない
            return False
        if context.defend_poke.nv_condition is not PokeNVCondition.EMPTY:
            # 状態異常なら変化しない
            return False
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
        return r < side_effect_ratio

    return check_side_effect_ratio


def launch_side_effect_freeze(context: MoveHandlerContext):
    """
    こおり
    :param context:
    :return:
    """
    context.field.put_record_other(f"追加効果: こおり")
    context.defend_poke.update_nv_condition(PokeNVCondition.FREEZE)
    return


def gen_check_side_effect_paralysis(side_effect_ratio: int, bodyslam: bool = False) -> Callable[
    [MoveHandlerContext], bool]:
    """
    追加効果でまひさせる技のハンドラ生成
    :param side_effect_ratio: 追加効果確率
    :param bodyslam: のしかかりのときTrue。ノーマルタイプがまひしなくなる。
    :return:
    """

    def check_side_effect_ratio(context: MoveHandlerContext):
        if bodyslam and PokeType.NORMAL in context.defend_poke.poke_types:
            # ノーマルタイプはのしかかりでまひしない
            return False
        if context.defend_poke.nv_condition is not PokeNVCondition.EMPTY:
            # 状態異常なら変化しない
            return False
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
        return r < side_effect_ratio

    return check_side_effect_ratio


def gen_launch_side_effect_nv_condition(nv_condition: PokeNVCondition):
    """
    状態異常にさせる追加効果の発動
    :param nv_condition:
    :return:
    """

    def launch_side_effect_nv_condition(context: MoveHandlerContext):
        """
        :param context:
        :return:
        """
        context.field.put_record_other(f"追加効果: {nv_condition}")
        context.defend_poke.update_nv_condition(nv_condition)
        return

    return launch_side_effect_nv_condition


def gen_check_side_effect_burn(side_effect_ratio: int) -> Callable[
    [MoveHandlerContext], bool]:
    """
    追加効果でやけどさせる技のハンドラ生成
    :param side_effect_ratio: 追加効果確率
    :return:
    """

    def check_side_effect_ratio(context: MoveHandlerContext):
        if PokeType.FIRE in context.defend_poke.poke_types:
            # ほのおタイプはやけどしない
            return False
        if context.defend_poke.nv_condition is not PokeNVCondition.EMPTY:
            # 状態異常なら変化しない
            return False
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
        return r < side_effect_ratio

    return check_side_effect_ratio


def gen_check_side_effect_poison(side_effect_ratio: int) -> Callable[
    [MoveHandlerContext], bool]:
    """
    追加効果でどくにさせる技のハンドラ生成
    :param side_effect_ratio: 追加効果確率
    :return:
    """

    def check_side_effect_ratio(context: MoveHandlerContext):
        if PokeType.POISON in context.defend_poke.poke_types:
            # どくタイプはどくにならない
            return False
        if context.defend_poke.nv_condition is not PokeNVCondition.EMPTY:
            # 状態異常なら変化しない
            return False
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
        return r < side_effect_ratio

    return check_side_effect_ratio


def check_hit_leechseed(context: MoveHandlerContext) -> bool:
    """
    やどりぎのタネ命中判定
    :param context:
    :return:
    """
    # 草タイプ、およびすでにやどりぎ状態の相手には効かない
    if PokeType.GRASS in context.defend_poke.poke_types:
        return False
    if context.defend_poke.v_leechseed:
        return False
    return _check_hit_by_avoidance(context)


def _check_hit_make_nv_condition(context: MoveHandlerContext) -> bool:
    """
    相手を状態異常にする技の基本命中判定
    :param context:
    :return:
    """
    if context.defend_poke.nv_condition is not PokeNVCondition.EMPTY:
        context.field.put_record_other("相手がすでに状態異常なので外れた")
        return False

    return _check_hit_by_avoidance(context)


def check_hit_hypnosis(context: MoveHandlerContext) -> bool:
    """
    さいみんじゅつ命中判定
    :param context:
    :return:
    """
    return _check_hit_make_nv_condition(context)


def launch_move_hypnosis(context: MoveHandlerContext):
    """
    さいみんじゅつ
    :param context:
    :return:
    """
    context.field.put_record_other(f"相手を眠らせる")
    # 2~8ターン眠る: 行動順がこの回数回ってきたタイミングで目覚めるが、目覚めたターンは行動なし
    sleep_turn = context.field.rng.gen(context.attack_player, GameRNGReason.SLEEP_TURN, 6) + 2
    context.defend_poke.update_nv_condition(PokeNVCondition.SLEEP, sleep_turn=sleep_turn)


def check_hit_make_poison(context: MoveHandlerContext) -> bool:
    """
    どくにさせる補助技命中判定
    :param context:
    :return:
    """
    if PokeType.POISON in context.defend_poke.poke_types:
        context.field.put_record_other("毒タイプは毒にならないので外れた")
        return False

    return _check_hit_make_nv_condition(context)


def gen_launch_move_make_poison(badly_poison: bool):
    """
    どくガス、どくどく
    :param context:
    :return:
    """

    def launch_move_make_poison(context: MoveHandlerContext):
        if badly_poison:
            context.field.put_record_other(f"相手を猛毒にする")
        else:
            context.field.put_record_other(f"相手を毒にする")
        context.defend_poke.update_nv_condition(PokeNVCondition.POISON, badly_poison=badly_poison)

    return launch_move_make_poison


def gen_check_hit_make_paralysis(thunderwave: bool):
    def check_hit_make_paralysis(context: MoveHandlerContext) -> bool:
        """
        まひにさせる補助技命中判定
        :param context:
        :return:
        """
        if thunderwave and PokeType.GROUND in context.defend_poke.poke_types:
            context.field.put_record_other("でんじはで地面タイプに外れた")
            return False

        return _check_hit_make_nv_condition(context)

    return check_hit_make_paralysis


def launch_move_make_paralysis(context: MoveHandlerContext):
    """
    まひにする
    :param context:
    :return:
    """
    context.defend_poke.update_nv_condition(PokeNVCondition.PARALYSIS)


def gen_check_hit_change_attacker_rank(rank_type: str, diff: int):
    """
    攻撃側のランクを変える補助技の命中判定
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def check_hit_change_attacker_rank(context: MoveHandlerContext) -> bool:
        poke = context.attack_poke
        if rank_type == "a":
            return poke.rank_a.can_incr(diff)
        if rank_type == "b":
            return poke.rank_b.can_incr(diff)
        if rank_type == "c":
            return poke.rank_c.can_incr(diff)
        if rank_type == "s":
            return poke.rank_s.can_incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.can_incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.can_incr(diff)

        raise ValueError

    return check_hit_change_attacker_rank


def gen_launch_move_change_attacker_rank(rank_type: str, diff: int):
    """
    攻撃側のランクを変える補助技の発動
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def launch_move_change_attacker_rank(context: MoveHandlerContext) -> bool:
        poke = context.attack_poke
        if rank_type == "a":
            return poke.rank_a.incr(diff)
        if rank_type == "b":
            return poke.rank_b.incr(diff)
        if rank_type == "c":
            return poke.rank_c.incr(diff)
        if rank_type == "s":
            return poke.rank_s.incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.incr(diff)

        raise ValueError

    return launch_move_change_attacker_rank


def gen_check_hit_change_defender_rank(rank_type: str, diff: int):
    """
    防御側のランクを変える補助技の命中判定
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def check_hit_change_defender_rank(context: MoveHandlerContext) -> bool:
        if not _check_hit_by_avoidance(context):
            return False
        poke = context.defend_poke
        if rank_type == "a":
            return poke.rank_a.can_incr(diff)
        if rank_type == "b":
            return poke.rank_b.can_incr(diff)
        if rank_type == "c":
            return poke.rank_c.can_incr(diff)
        if rank_type == "s":
            return poke.rank_s.can_incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.can_incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.can_incr(diff)

        raise ValueError

    return check_hit_change_defender_rank


def gen_launch_move_change_defender_rank(rank_type: str, diff: int):
    """
    攻撃側のランクを変える補助技の発動
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def launch_move_change_defender_rank(context: MoveHandlerContext) -> bool:
        poke = context.defend_poke
        if rank_type == "a":
            return poke.rank_a.incr(diff)
        if rank_type == "b":
            return poke.rank_b.incr(diff)
        if rank_type == "c":
            return poke.rank_c.incr(diff)
        if rank_type == "s":
            return poke.rank_s.incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.incr(diff)

        raise ValueError

    return launch_move_change_defender_rank


def gen_check_side_effect_change_defender_rank(rank_type: str, diff: int):
    """
    防御側のランクを変える追加効果判定
    初代では33.2%の確率しかない。
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def check_side_effect_change_defender_rank(context: MoveHandlerContext) -> bool:
        r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 255)
        # 85 / 256 = 0.332
        if r > 84:
            return False
        poke = context.defend_poke
        if rank_type == "a":
            return poke.rank_a.can_incr(diff)
        if rank_type == "b":
            return poke.rank_b.can_incr(diff)
        if rank_type == "c":
            return poke.rank_c.can_incr(diff)
        if rank_type == "s":
            return poke.rank_s.can_incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.can_incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.can_incr(diff)

        raise ValueError

    return check_side_effect_change_defender_rank


def gen_launch_side_effect_change_defender_rank(rank_type: str, diff: int):
    """
    防御側のランクを変える追加効果の発動
    :param rank_type: どのランクを変更するか。a,b,c,s,accuracy,evasion
    :param diff: 変化させたい量
    :return:
    """

    def launch_side_effect_change_defender_rank(context: MoveHandlerContext) -> bool:
        poke = context.defend_poke
        if rank_type == "a":
            return poke.rank_a.incr(diff)
        if rank_type == "b":
            return poke.rank_b.incr(diff)
        if rank_type == "c":
            return poke.rank_c.incr(diff)
        if rank_type == "s":
            return poke.rank_s.incr(diff)
        if rank_type == "accuracy":
            return poke.rank_accuracy.incr(diff)
        if rank_type == "evasion":
            return poke.rank_evasion.incr(diff)

        raise ValueError

    return launch_side_effect_change_defender_rank


def check_hit_confuse(context: MoveHandlerContext) -> bool:
    if not _check_hit_by_avoidance(context):
        return False
    if context.defend_poke.v_confuse:
        return False
    return True


def launch_move_confuse(context: MoveHandlerContext):
    # 1~7ターン混乱する: 行動順ごとに1デクリメントし、0になったときに解除。解除ターンは必ず攻撃できる。
    confuse_turn = context.field.rng.gen(context.attack_player, GameRNGReason.CONFUSE_TURN, 6) + 1
    context.defend_poke.v_confuse_remaining_turn = confuse_turn


def check_side_effect_confuse(context: MoveHandlerContext) -> bool:
    """
    10%で相手を混乱させる追加効果
    :param context:
    :return:
    """
    r = context.field.rng.gen(context.attack_player, GameRNGReason.SIDE_EFFECT, 99)
    if r > 9:
        return False
    if context.defend_poke.v_confuse:
        return False
    return True


def launch_side_effect_confuse(context: MoveHandlerContext):
    # 1~7ターン混乱する: 行動順ごとに1デクリメントし、0になったときに解除。解除ターンは必ず攻撃できる。
    confuse_turn = context.field.rng.gen(context.attack_player, GameRNGReason.CONFUSE_TURN, 6) + 1
    context.defend_poke.v_confuse_remaining_turn = confuse_turn


def launch_move_leechseed(context: MoveHandlerContext):
    """
    やどりぎ状態にする
    :param context:
    :return:
    """
    context.defend_poke.v_leechseed = True


def check_hit_recover(context: MoveHandlerContext) -> bool:
    """
    じこさいせいの命中判定
    HP満タンだと失敗
    :param context:
    :return:
    """
    if context.attack_poke.hp == context.attack_poke.max_hp:
        context.field.put_record_other("体力満タンなので失敗")
        return False
    return True


def launch_move_recover(context: MoveHandlerContext):
    """
    じこさいせい
    :param context:
    :return:
    """
    max_recover = context.attack_poke.max_hp - context.attack_poke.hp
    recover = min(max_recover, context.attack_poke.max_hp // 2)
    context.field.put_record_other(f"回復ダメージ: {recover}")
    context.attack_poke.hp_incr(recover)


def check_hit_dreameater(context: MoveHandlerContext):
    """
    ゆめくい命中判定
    :param context:
    :return:
    """
    if context.defend_poke.nv_condition is not PokeNVCondition.SLEEP:
        context.field.put_record_other("相手が眠りでないので外れた")
        return False

    return check_hit_attack_default(context)


def check_hit_rest(context: MoveHandlerContext) -> bool:
    """
    ねむるの命中判定
    HP満タンだと失敗
    自分が状態異常でもOK
    :param context:
    :return:
    """
    if context.attack_poke.hp == context.attack_poke.max_hp:
        context.field.put_record_other("体力満タンなので失敗")
        return False
    return True


def launch_move_rest(context: MoveHandlerContext):
    """
    眠る
    :param context:
    :return:
    """
    recover = context.attack_poke.max_hp - context.attack_poke.hp
    context.field.put_record_other(f"回復: {recover}")
    context.attack_poke.hp_incr(recover)
    sleep_turn = 2  # 1回眠る、1回起きる、その次行動
    context.attack_poke.update_nv_condition(PokeNVCondition.SLEEP, sleep_turn=sleep_turn, force_sleep=True)


def check_hit_reflect(context: MoveHandlerContext) -> bool:
    """
    リフレクター命中判定
    リフレクター状態でなければ成功
    :param context:
    :return:
    """
    if context.attack_poke.v_reflect:
        context.field.put_record_other("すでにリフレクター状態なので失敗")
        return False
    return True


def launch_move_reflect(context: MoveHandlerContext):
    """
    リフレクター
    :param context:
    :return:
    """
    context.attack_poke.v_reflect = True


def check_hit_lightscreen(context: MoveHandlerContext) -> bool:
    """
    ひかりのかべ命中判定
    ひかりのかべ状態でなければ成功
    :param context:
    :return:
    """
    if context.attack_poke.v_lightscreen:
        context.field.put_record_other("すでにひかりのかべ状態なので失敗")
        return False
    return True


def launch_move_lightscreen(context: MoveHandlerContext):
    """
    ひかりのかべ
    :param context:
    :return:
    """
    context.attack_poke.v_lightscreen = True
