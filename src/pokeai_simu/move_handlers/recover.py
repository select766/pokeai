# -*- coding:utf-8 -*-

"""
体力回復技
じこさいせい
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .friend_non_attack import MoveHandlerFriendNonAttack
from .. import type_match


class MoveHandlerRecover(MoveHandlerFriendNonAttack):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)

    def _can_effect(self):
        """
        仮に発動すると効果があるかどうかを判定
        """
        if self.move_entry.move_id is MoveID.Recover:
            return self.friend_poke.hp < self.friend_poke.static_param.max_hp
        raise NotImplementedError()

    def _do_effect(self):
        """
        発動してポケモンの状態を変化させる
        """
        if self.move_entry.move_id is MoveID.Recover:
            self._log_msg("体力を回復した")
            # 1/2切り捨てを回復
            max_gain = self.friend_poke.calc_ratio_damage(8)
            self.friend_poke.hp += max_gain
