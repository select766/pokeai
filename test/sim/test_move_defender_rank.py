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


class TestMoveDefenderRank(unittest.TestCase):
    """
    防御側のランクが変わる技
    """

    def test_basic(self):
        """
        最も基本的なダメージ計算
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.VINEWHIP, Move.GROWL, Move.STRINGSHOT])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.WATERGUN, Move.SCREECH, Move.SANDATTACK])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=2),
                               FieldAction(FieldActionType.MOVE, move_idx=2)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ0
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146)
        # BULBASAUR: B-2, CHARMANDER: A-1

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ23 A-1 B-2
        self.assertEqual(field.parties[0].get().hp, 152 - 23)
        # BULBASAUR -> CHARMANDER: ダメージ18
        self.assertEqual(field.parties[1].get().hp, 146 - 18)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ8
        self.assertEqual(field.parties[0].get().hp, 152 - 23 - 8)
        # BULBASAUR -> CHARMANDER: ダメージ14
        self.assertEqual(field.parties[1].get().hp, 146 - 18 - 14)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=3),
                               FieldAction(FieldActionType.MOVE, move_idx=3)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        self.assertEqual(field.parties[0].get().rank_accuracy.value, -1)
        self.assertEqual(field.parties[1].get().eff_s(), 78)

        # 急所: 補正無効
        rng.enqueue_const(0, GameRNGReason.CRITICAL, 0)
        rng.enqueue_const(1, GameRNGReason.CRITICAL, 0)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ32
        self.assertEqual(field.parties[0].get().hp, 152 - 23 - 8 - 32)
        # BULBASAUR -> CHARMANDER: ダメージ33
        self.assertEqual(field.parties[1].get().hp, 146 - 18 - 14 - 33)
