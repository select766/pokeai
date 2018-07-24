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


class TestMoveAttackBurn(unittest.TestCase):
    """
    やけどさせる攻撃技
    """

    def test_basic(self):
        """
        追加効果でやけどになる。
        攻撃力が下がる。
        スリップダメージを受ける。
        ほのおタイプはやけどしない。
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.EMBER])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.EMBER])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ50、スリップダメージ152//16=9
        self.assertEqual(field.parties[0].get().hp, 152 - 50 - 9)
        # やけど
        # BULBASAUR -> CHARMANDER: ダメージ9(この時点で攻撃ダウン反映)
        self.assertEqual(field.parties[1].get().hp, 146 - 9)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.BURN)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.EMPTY)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17、スリップダメージ152//16=9
        self.assertEqual(field.parties[0].get().hp, 152 - 50 - 9 - 17 - 9)
        # BULBASAUR -> CHARMANDER: ダメージ11(特殊技は攻撃ダウンなし)
        self.assertEqual(field.parties[1].get().hp, 146 - 9 - 11)
        # やけどしない
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.BURN)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.EMPTY)
