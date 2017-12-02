# -*- coding:utf-8 -*-

"""
自分にかける補助技
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .. import type_match


class MoveHandlerFriendNonAttack(MoveHandler):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)

    def _run(self):
        # 行動可能判定
        can_move = self._check_if_possible_to_move()
        if not can_move:
            return

        if not self._can_effect():
            self._log_msg("こうかはないようだ(発動しても効果なし)")
            return

        # 自分にかける場合は命中判定がない

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
