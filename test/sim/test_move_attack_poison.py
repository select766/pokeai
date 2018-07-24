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


class TestMoveAttackPoison(unittest.TestCase):
    """
    どくにさせる攻撃技
    """

    def test_basic(self):
        """
        追加効果でどくになる。
        スリップダメージを受ける。
        どくタイプはやけどしない。
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.SLUDGE])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.SLUDGE])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ31
        self.assertEqual(field.parties[0].get().hp, 152 - 31)
        # どくにならない
        # BULBASAUR -> CHARMANDER: ダメージ48、まだスリップダメージなし
        self.assertEqual(field.parties[1].get().hp, 146 - 48)
        # どくになる
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.EMPTY)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.POISON)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 31 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ18、スリップダメージ146//16=9
        self.assertEqual(field.parties[1].get().hp, 146 - 48 - 18 - 9)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.EMPTY)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.POISON)
