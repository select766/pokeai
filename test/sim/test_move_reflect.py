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


class TestMoveReflect(unittest.TestCase):
    """
    リフレクター、ひかりのかべ
    """

    def test_basic(self):
        """
        最も基本的なダメージ計算
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.REFLECT, Move.LIGHTSCREEN])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.SURF])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146 - 0)
        self.assertEqual(field.parties[0].get().v_reflect, True)
        self.assertEqual(field.parties[0].get().v_lightscreen, False)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ10
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 10)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146 - 0)
        self.assertEqual(field.parties[0].get().v_reflect, True)
        self.assertEqual(field.parties[0].get().v_lightscreen, False)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ19(特殊技は効果なし)
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 10 - 19)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146 - 0)
        self.assertEqual(field.parties[0].get().v_reflect, True)
        self.assertEqual(field.parties[0].get().v_lightscreen, True)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ10
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 10 - 19 - 10)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146 - 0)
        self.assertEqual(field.parties[0].get().v_reflect, True)
        self.assertEqual(field.parties[0].get().v_lightscreen, True)
