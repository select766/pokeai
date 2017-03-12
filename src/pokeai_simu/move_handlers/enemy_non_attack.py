# -*- coding:utf-8 -*-

"""
敵にかける補助技
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .. import type_match


class MoveHandlerEnemyNonAttack(MoveHandler):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)
        self.check_type_match = False  # 「でんじは」は相性チェックあり

    def _run(self):
        # 行動可能判定
        can_move = self._check_if_possible_to_move()
        if not can_move:
            return

        if not self._can_effect():
            self._log_msg("こうかはないようだ(発動しても効果なし)")
            return

        # 相性判定
        if self.check_type_match:
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

        self._do_effect()

    def _can_effect(self):
        """
        仮に発動すると効果があるかどうかを判定
        """
        raise NotImplementedError()

    def _do_effect(self):
        """
        発動してポケモンの状態を変化させる
        """
        raise NotImplementedError()
