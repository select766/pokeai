import unittest

from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGFixed, GameRNGReason
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke import PokeNVCondition
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType


class TestMoveAttackFreeze(unittest.TestCase):
    """
    凍らせる攻撃技
    """

    def test_basic(self):
        """
        :return:
        """

        # H:146,A:104,B:95,C:102,S:117
        poke_atk = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.BLIZZARD])
        # H:157,A:147,B:232,C:137,S:122
        poke_def = PokeStatic.create(Dexno.CLOYSTER, [Move.TACKLE, Move.BLIZZARD])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 146)
        self.assertEqual(field.parties[1].get().hp, 157)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CLOYSTER -> CHARMANDER : ダメージ25
        self.assertEqual(field.parties[0].get().hp, 146 - 25)
        # CHARMANDER -> CLOYSTER: ダメージ10
        # こおりタイプなのでこおらない
        self.assertEqual(field.parties[1].get().hp, 157 - 10)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CLOYSTER -> CHARMANDER : ダメージ54
        # 氷→炎は当時等倍
        self.assertEqual(field.parties[0].get().hp, 146 - 25 - 108)
        # CHARMANDER -> CLOYSTER: こおってうごかない
        self.assertEqual(field.parties[1].get().hp, 157 - 10)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.FREEZE)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.EMPTY)
