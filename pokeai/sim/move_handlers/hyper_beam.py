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
            super()._run()  # self.hyper_beam_kickbackがセットされる
        else:
            # 反動ターン
            self._log_msg("はんどうでうごけない")
            self.hyper_beam_kickback = False
