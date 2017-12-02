# -*- coding:utf-8 -*-

"""
自分の能力を変化させる技
リフレクター・かげぶんしん・はねる
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .friend_non_attack import MoveHandlerFriendNonAttack
from .. import type_match


class MoveHandlerDoubleTeam(MoveHandlerFriendNonAttack):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)

    def _can_effect(self):
        """
        仮に発動すると効果があるかどうかを判定
        """
        if self.move_entry.move_id is MoveID.Reflect:
            return not self.friend_poke.reflect
        elif self.move_entry.move_id is MoveID.DoubleTeam:
            return self.friend_poke.rank_evasion < 6
        elif self.move_entry.move_id is MoveID.Splash:
            # はねるだが、発動はする扱い
            return True
        raise NotImplementedError()

    def _do_effect(self):
        """
        発動してポケモンの状態を変化させる
        """
        if self.move_entry.move_id is MoveID.Reflect:
            self._log_msg("リフレクターをはった")
            # リフレクター状態になる
            self.friend_poke.reflect = True
        elif self.move_entry.move_id is MoveID.DoubleTeam:
            self._log_msg("回避率があがった")
            self.friend_poke.rank_evasion += 1
        elif self.move_entry.move_id is MoveID.Splash:
            self._log_msg("なにもおこらない")
