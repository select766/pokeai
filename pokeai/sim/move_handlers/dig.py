# -*- coding:utf-8 -*-

"""
1ターン目にためて、2ターン目にダメージを与える技
あなをほる
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .. import type_match
from .attack import MoveHandlerAttack

class MoveHandlerDig(MoveHandlerAttack):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)
        self.dig_charging = False
    
    def is_continuing(self):
        return self.dig_charging

    def _run(self):
        if self.dig_charging:
            # 攻撃ターン
            self.dig_charging = False
            self.friend_poke.digging = False
            super()._run()
        else:
            # 準備ターン
            # 行動可能なら行動し、あなをほる状態になる
            # 行動可能判定
            can_move = self._check_if_possible_to_move()
            if not can_move:
                return

            self.dig_charging = True
            if self.move_entry.move_id is MoveID.Dig:
                self._log_msg("あなをほってじめんにもぐった")
                self.friend_poke.digging = True
                # TODO: あなをほる状態が解除されないフローがないかチェック
