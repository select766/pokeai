# -*- coding:utf-8 -*-

"""
通常攻撃技
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .. import type_match


class MoveHandlerAttack(MoveHandler):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)

    def _run(self):
        # 行動可能判定
        can_move = self._check_if_possible_to_move()
        if not can_move:
            return

        # 相性判定
        have_effect_as_type = type_match.can_effect(
            self.move_entry.move_poke_type, self.enemy_poke)
        if not have_effect_as_type:
            self._log_msg("こうかはないようだ")
            return

        # 命中判定
        is_hit = self._check_hit_by_accuracy(self.move_entry.accuracy)
        if not is_hit:
            self._log_msg("こうげきははずれた")
            return

        # 連続攻撃技
        # https://wiki.ポケモン.com/wiki/%E9%80%A3%E7%B6%9A%E6%94%BB%E6%92%83%E6%8A%80
        if self.move_entry.move_id is MoveID.DoubleKick:
            attack_count = 2
        else:
            attack_count = 1

        actual_attack_count = 0
        total_damage = 0
        for attack_cycle in range(attack_count):
            if self.enemy_poke.hp <= 0:
                # 連続攻撃技で、途中であいてが倒れた場合
                break
            # 急所判定
            critical_ratio = self.friend_poke.static_param.base_s // 2
            if self.move_entry.move_id in [MoveID.Slash]:
                # TODO:急所に当たりやすい技
                critical_ratio *= 8
            critical_ratio = min(critical_ratio, 255)
            is_critical = critical_ratio > self.field.rng.get(
                self.friend_player, BattleRngReason.Critical)
            if is_critical:
                self._log_msg("きゅうしょにあたった")

            # ダメージ判定
            raw_damage = self._calc_damage(
                self.move_entry.attack, self.move_entry.move_poke_type, self.friend_poke, self.enemy_poke, is_critical)
            if raw_damage <= 0:
                # はずれとみなされる
                damage = 0
                self._log_msg("こうげきははずれた (ダメージ計算=0)")
            else:
                damage = min(raw_damage, self.enemy_poke.hp)
                self._log_msg("ダメージ: {}".format(damage))
                self.enemy_poke.hp -= damage

            total_damage += damage
            actual_attack_count += 1

        if attack_count > 1:
            self._log_msg("{} かいあたった".format(actual_attack_count))

        # 追加効果判定
        return
