# -*- coding:utf-8 -*-

"""
相手を状態異常/こんらんにする技
どくどく・あくまのキッス・でんじは・あやしいひかり
"""

from ..poke_type import PokeType
from ..poke import Poke, PokeNVCondition
from ..move_id import MoveID
from ..battle_rng import BattleRng, BattleRngReason
from .move_handler import MoveHandler
from .enemy_non_attack import MoveHandlerEnemyNonAttack
from .. import type_match


class MoveHandlerToxic(MoveHandlerEnemyNonAttack):
    def __init__(self, field, move_entry):
        super().__init__(field, move_entry)
        if move_entry.move_id is MoveID.ThunderWave:
            self.check_type_match = True  # 「でんじは」は相性チェックあり

    def _can_effect(self):
        """
        仮に発動すると効果があるかどうかを判定
        状態異常はタイプにより無効な場合がある
        """
        if self.move_entry.move_id is MoveID.ConfuseRay:
            if self.enemy_poke.confusion_turn == 0:
                return True
            else:
                self._log_msg("すでにこんらんしている")
                return False
        elif self.move_entry.move_id in [MoveID.Toxic]:
            return self.enemy_poke.can_poisoned
        elif self.move_entry.move_id in [MoveID.LovelyKiss]:
            return self.enemy_poke.can_sleep
        elif self.move_entry.move_id in [MoveID.ThunderWave]:
            return self.enemy_poke.can_paralyzed
        elif self.move_entry.move_id in []:
            return self.enemy_poke.can_burned
        raise NotImplementedError()

    def _do_effect(self):
        """
        発動してポケモンの状態を変化させる
        """
        if self.move_entry.move_id is MoveID.ConfuseRay:
            # 1~7
            confusion_turn = self.field.rng.get(
                self.friend_player, BattleRngReason.ConfusionTurn, top=6) + 1
            self.enemy_poke.confusion_turn = confusion_turn
        elif self.move_entry.move_id is MoveID.ThunderWave:
            self.enemy_poke.nv_condition = PokeNVCondition.Paralysis
        elif self.move_entry.move_id is MoveID.LovelyKiss:
            self.enemy_poke.nv_condition = PokeNVCondition.Sleep
            # 2~8
            sleep_turn = self.field.rng.get(
                self.friend_player, BattleRngReason.SleepTurn, top=6) + 2
            self.enemy_poke.sleep_turn = sleep_turn
        elif self.move_entry.move_id is MoveID.Toxic:
            self.enemy_poke.nv_condition = PokeNVCondition.Poison
            self.enemy_poke.bad_poison = True
            self.enemy_poke.bad_poison_turn = 0
        else:
            raise NotImplementedError()
