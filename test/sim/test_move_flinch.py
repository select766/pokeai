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


class TestMoveAttackFlinch(unittest.TestCase):
    """
    ひるませる攻撃技
    """

    def test_basic(self):
        """
        最も基本的なダメージ計算
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.BITE, Move.TACKLE])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.BITE, Move.TACKLE])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ29
        self.assertEqual(field.parties[0].get().hp, 152 - 29)
        # 怯み発生
        # BULBASAUR -> CHARMANDER: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 146)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 29 - 17)
        # 怯みは解除済み
        # BULBASAUR -> CHARMANDER: ダメージ30
        self.assertEqual(field.parties[1].get().hp, 146 - 30)
        # 後攻でひるませるが次ターンに影響なし

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        # 怯みは解除済み
        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 29 - 17 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ18
        self.assertEqual(field.parties[1].get().hp, 146 - 30 - 18)
