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


class TestMoveConst(unittest.TestCase):
    """
    固定ダメージ技（一撃必殺含む）
    """

    def test_const(self):
        """
        最も基本的なダメージ計算
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.SONICBOOM])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.DRAGONRAGE])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ40
        self.assertEqual(field.parties[0].get().hp, 152 - 40)
        # BULBASAUR -> CHARMANDER: ダメージ20
        self.assertEqual(field.parties[1].get().hp, 146 - 20)

    def test_type_match(self):
        """
        タイプ相性で無効、ばつぐんでもダメージは変わらない
        :return:
        """

        # H:148
        poke_atk = PokeStatic.create(Dexno.DRATINI, [Move.SONICBOOM])  # ミニリュウ
        # H:137
        poke_def = PokeStatic.create(Dexno.GASTLY, [Move.DRAGONRAGE])  # ゴース
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 148)
        self.assertEqual(field.parties[1].get().hp, 137)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # GASTLY -> DRATINI : ダメージ40
        self.assertEqual(field.parties[0].get().hp, 148 - 40)
        # DRATINI -> GASTLY: ダメージ0
        self.assertEqual(field.parties[1].get().hp, 137 - 0)

    def test_fissure(self):
        """
        一撃必殺
        素早さが低いと当たらない
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.FISSURE, Move.AGILITY])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.SPLASH])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR: ダメージなし
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> CHARMANDER: ダメージなし
        self.assertEqual(field.parties[1].get().hp, 146)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR: ダメージなし
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> CHARMANDER: ダメージなし
        self.assertEqual(field.parties[1].get().hp, 146)

        # 素早さを上げたので当たる
        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.GAME_END)

        # CHARMANDER -> BULBASAUR: ダメージなし
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> CHARMANDER: 一撃必殺
        self.assertEqual(field.parties[1].get().hp, 0)
