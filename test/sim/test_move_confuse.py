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


class TestMoveConfuse(unittest.TestCase):
    """
    こんらん
    """

    def test_basic(self):
        """
        こんらんによる自滅
        自分のランク補正でダメージ変動
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.SWORDSDANCE])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.CONFUSERAY, Move.LEER])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        rng.enqueue_const(1, GameRNGReason.CONFUSE_TURN, 3)  # 3回混乱で自傷の可能性がある
        rng.enqueue_const(0, GameRNGReason.MOVE_CONFUSE, 1)  # 自傷せず
        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : 混乱させる、自傷せずA+2
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> CHARMANDER: 0
        self.assertEqual(field.parties[1].get().hp, 146)
        self.assertEqual(field.parties[0].get().v_confuse, True)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : 混乱させる、効果なし、自傷ダメージ37
        self.assertEqual(field.parties[0].get().hp, 152 - 37)
        # BULBASAUR -> CHARMANDER: 0
        self.assertEqual(field.parties[1].get().hp, 146)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : B-1、自傷ダメージ55
        self.assertEqual(field.parties[0].get().hp, 152 - 37 - 55)
        # BULBASAUR -> CHARMANDER: 0
        self.assertEqual(field.parties[1].get().hp, 146)
        self.assertEqual(field.parties[0].get().v_confuse, True)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : 0
        self.assertEqual(field.parties[0].get().hp, 152 - 37 - 55)
        # BULBASAUR -> CHARMANDER: 混乱解消、ダメージ34
        self.assertEqual(field.parties[1].get().hp, 146 - 34)
        self.assertEqual(field.parties[0].get().v_confuse, False)
