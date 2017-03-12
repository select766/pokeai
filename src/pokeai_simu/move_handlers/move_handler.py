# -*- coding:utf-8 -*-

"""
技の効果処理の基底クラス
"""

from ..poke import Poke, PokeNVCondition
from ..poke_type import PokeType
from .. import type_match
from ..battle_rng import BattleRng, BattleRngReason
from ..field_log import FieldLog, FieldLogReason, FieldLogSender


class MoveHandler(object):
    def __init__(self, field, move_entry):
        self.field = field
        self.move_entry = move_entry

    def is_continuing(self):
        return False

    def run(self, move_order, friend_player, friend_poke, enemy_poke):
        self.move_order = move_order
        self.friend_player = friend_player
        self.friend_poke = friend_poke
        self.enemy_poke = enemy_poke
        self._run()

    def _run(self):
        """
        技種類ごとの処理
        """
        raise NotImplementedError()

    def _check_if_possible_to_move(self):
        """
        行動が可能か決定する
        対象 状態異常・こんらん
        """
        friend_poke = self.friend_poke
        if friend_poke.nv_condition is PokeNVCondition.Freeze:
            self._log_msg("こおってしまってうごかない")
            return False

        if friend_poke.nv_condition is PokeNVCondition.Sleep:
            friend_poke.sleep_turn -= 1
            if friend_poke.sleep_turn > 0:
                self._log_msg("ぐうぐうねむっている")
                return False
            else:
                friend_poke.nv_condition = PokeNVCondition.Empty
                self._log_msg("めをさました")
                # 初代では目を覚ますだけで行動できない
                return False

        if friend_poke.confusion_turn > 0:
            self._log_msg("こんらんしている")
            friend_poke.confusion_turn -= 1
            if friend_poke.confusion_turn > 0:
                if self.field.rng.get(self.friend_player, BattleRngReason.Paralysis) < 128:
                    # 1/2で行動不能
                    self._log_msg("こんらんで自分に攻撃")
                    # TODO 自分へのダメージ
                    return False
            else:
                self._log_msg("こんらんが とけた")

        if friend_poke.nv_condition is PokeNVCondition.Paralysis:
            if self.field.rng.get(self.friend_player, BattleRngReason.Paralysis) < 52:
                # 1/5の確率で行動不能
                self._log_msg("からだがしびれてうごけない")
                return False

        return True

    def _log_msg(self, message):
        self.field.logger.write(
            FieldLog(FieldLogSender.MoveHandler, FieldLogReason.Empty, None, message))

    def _calc_damage(self, attack, move_poke_type, friend_poke, enemy_poke, critical):
        """
        ダメージ計算コア
        """
        if move_poke_type in [PokeType.Normal, PokeType.Fight, PokeType.Poison, PokeType.Ground, PokeType.Flying, PokeType.Bug, PokeType.Rock, PokeType.Ghost]:
            # ぶつりわざ
            friend_a = friend_poke.eff_a(critical)
            enemy_b = enemy_poke.eff_b(critical)
            if enemy_poke.reflect:
                friend_a = friend_a // 4
                enemy_b = enemy_b // 2
        else:
            # とくしゅわざ
            friend_a = friend_poke.eff_c(critical)
            enemy_b = enemy_poke.eff_c(critical)
            # TODO: ひかりのかべ
        friend_level = friend_poke.static_param.level
        critical_bonus = 2 if critical else 1
        # 217 to 255
        d_random = 217 + \
            self.field.rng.get(self.friend_player,
                               BattleRngReason.DamageRandom, top=38)

        damage = attack * friend_a * \
            (friend_level * critical_bonus * 2 // 5 + 2) // enemy_b // 50 + 2
        # 係数をかけるごとに切り捨て
        type_bonus = type_match.friend_type_bonus_x2(
            move_poke_type, friend_poke)
        type_match_1 = type_match.get_type_match_x2(
            move_poke_type, enemy_poke.type1)
        type_match_2 = type_match.get_type_match_x2(
            move_poke_type, enemy_poke.type2)
        damage = damage * type_bonus // 2
        damage = damage * type_match_1 // 2
        damage = damage * type_match_2 // 2
        damage = damage * d_random // 255
        return damage

    def _check_hit_by_accuracy(self):
        """
        技が命中するかどうかの判定
        ランク補正込みの命中率で判定
        考慮:
        あなをほる
        """
        if self.enemy_poke.digging:
            # あなをほる状態なのであたらない
            # TODO: そらをとぶ
            return False
        # 技の命中率×自分のランク補正(命中率)÷相手のランク補正(回避率)
        hit_ratio_table = {100: 255, 95: 242, 90: 229, 85: 216,
                           80: 204, 75: 191, 70: 178, 60: 152, 55: 140, 50: 127, 0: 0}
        hit_ratio = hit_ratio_table[self.move_entry.accuracy]
        hit_ratio = hit_ratio * 2 // (self.friend_poke.rank_accuracy + 2)
        hit_ratio = hit_ratio * 2 // (self.enemy_poke.rank_evasion + 2)

        # 1 to 255
        hit_judge_rnd = self.field.rng.get(
            self.friend_player, BattleRngReason.Hit, top=254) + 1
        is_hit = hit_judge_rnd < hit_ratio
        return is_hit
