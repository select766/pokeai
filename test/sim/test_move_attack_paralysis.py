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


class TestMoveAttackParalysis(unittest.TestCase):
    """
    まひさせる攻撃技
    """

    def test_basic(self):
        """
        追加効果でまひになる。
        素早さが変化し攻撃順序が変わる。
        乱数によって行動不能。
        のしかかりでノーマルタイプはまひしない。
        :return:
        """

        # H:267,A:162,B:117,C:117,S:82
        # カビゴン
        poke_atk = PokeStatic.create(Dexno.SNORLAX, [Move.TACKLE, Move.THUNDERSHOCK, Move.BODYSLAM])
        # H:172,A:135,B:109,C:137,S:157
        # エレブー
        poke_def = PokeStatic.create(Dexno.ELECTABUZZ, [Move.TACKLE, Move.THUNDERSHOCK, Move.BODYSLAM])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 267)
        self.assertEqual(field.parties[1].get().hp, 172)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=2),
                               FieldAction(FieldActionType.MOVE, move_idx=2)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # ELECTABUZZ -> SNORLAX : ダメージ45
        self.assertEqual(field.parties[0].get().hp, 267 - 45)
        # ノーマルタイプなのでまひしない
        # SNORLAX -> ELECTABUZZ: ダメージ85
        # まひ
        self.assertEqual(field.parties[1].get().hp, 172 - 85)

        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.EMPTY)
        self.assertEqual(field.parties[1].get().nv_condition, PokeNVCondition.PARALYSIS)
        # すばやさが下がっている
        self.assertEqual(field.parties[1].get().eff_s(), 157 // 4)

        # まひだけど行動可能
        rng.enqueue_const(1, GameRNGReason.MOVE_PARALYSIS, 3)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # ELECTABUZZ -> SNORLAX : ダメージ33
        # まひ
        self.assertEqual(field.parties[0].get().hp, 267 - 45 - 33)
        # SNORLAX -> ELECTABUZZ: ダメージ85
        self.assertEqual(field.parties[1].get().hp, 172 - 85 - 36)

        # まひでお互い動けない
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        self.assertEqual(field.parties[0].get().hp, 267 - 45 - 33)
        self.assertEqual(field.parties[1].get().hp, 172 - 85 - 36)
