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


class TestMoveAttackerRank(unittest.TestCase):
    """
    攻撃側のランクが変わる技
    """

    def test_basic(self):
        """
        最も基本的なダメージ計算
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.VINEWHIP, Move.SWORDSDANCE, Move.AGILITY])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.WATERGUN, Move.AMNESIA, Move.DEFENSECURL])
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
        # BULBASAUR: A+2, CHARMANDER: C+2

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ34 A+2
        self.assertEqual(field.parties[1].get().hp, 146 - 34)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=3),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ16 C+2
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 16)
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146 - 34)
        # BULBASAUR: A+2, S+2, CHARMANDER: C+2

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=3)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ0
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 16)
        # BULBASAUR -> CHARMANDER: ダメージ34
        # BULBASAURが先制するので、防御を上げる前に攻撃が通る
        self.assertEqual(field.parties[1].get().hp, 146 - 34 - 34)
        # BULBASAUR: A+2, S+2, CHARMANDER: C+2, B+1

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 16 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ23
        self.assertEqual(field.parties[1].get().hp, 146 - 34 - 34 - 23)
        # BULBASAUR: A+2, S+2, CHARMANDER: C+2, B+1

        # 急所: 補正無効
        rng.enqueue_const(0, GameRNGReason.CRITICAL, 0)
        rng.enqueue_const(1, GameRNGReason.CRITICAL, 0)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        # CHARMANDER -> BULBASAUR : ダメージ32
        self.assertEqual(field.parties[0].get().hp, 152 - 17 - 16 - 17 - 32)
        # BULBASAUR -> CHARMANDER: ダメージ33
        self.assertEqual(field.parties[1].get().hp, 146 - 34 - 34 - 23 - 33)
