import unittest

from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGFixed, GameRNGReason
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType


class TestMoveRecover(unittest.TestCase):
    """
    じこさいせい
    """

    def test_basic(self):
        """
        じこさいせい
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.RECOVER])
        # H:267,A:162,B:117,C:117,S:82
        # カビゴン
        poke_def = PokeStatic.create(Dexno.SNORLAX, [Move.MEGAKICK, Move.SPLASH])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 267)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # SNORLAX -> BULBASAUR: 回復なし、ダメージ129
        self.assertEqual(field.parties[0].get().hp, 152 - 129)
        # BULBASAUR -> SNORLAX: ダメージなし
        self.assertEqual(field.parties[1].get().hp, 267)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # SNORLAX -> BULBASAUR: 回復152//2=76
        self.assertEqual(field.parties[0].get().hp, 152 - 129 + 76)
        # BULBASAUR -> SNORLAX: ダメージなし
        self.assertEqual(field.parties[1].get().hp, 267)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # SNORLAX -> BULBASAUR: 回復152//2=76, HP上限でクリップ
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> SNORLAX: ダメージなし
        self.assertEqual(field.parties[1].get().hp, 267)
