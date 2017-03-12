# -*- coding:utf-8 -*-

"""
1ターン目で攻撃、2ターン目で反動の攻撃
はかいこうせん
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .. import type_match
from .attack import MoveHandlerAttack


class MoveHandlerHyperBeam(MoveHandlerAttack):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)
        self.hyper_beam_kickback = False

    def is_continuing(self):
        return self.hyper_beam_kickback

    def _run(self):
        if not self.hyper_beam_kickback:
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
            is_hit = self._check_hit_by_accuracy()
            if not is_hit:
                self._log_msg("こうげきははずれた")
                return

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
                return
            else:
                damage = min(raw_damage, self.enemy_poke.hp)
                self._log_msg("ダメージ: {}".format(damage))
                self.enemy_poke.hp -= damage

            if self.enemy_poke.hp > 0:
                # 相手を倒すと反動なし
                self.hyper_beam_kickback = True
                self._log_msg("次のターンは反動")
            else:
                self._log_msg("倒したので反動なし")

            return
        else:
            # 反動ターン
            self._log_msg("はんどうでうごけない")
            self.hyper_beam_kickback = False
