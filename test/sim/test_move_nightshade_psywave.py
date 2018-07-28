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


class TestMoveNightshadePsywave(unittest.TestCase):
    """
    ナイトヘッド・サイコウェーブ
    レベル依存の固定ダメージ技
    """

    def test_basic(self):
        """
        相性無視
        :return:
        """

        # H:267,A:162,B:117,C:117,S:82
        # カビゴン
        poke_atk = PokeStatic.create(Dexno.SNORLAX, [Move.PSYWAVE])
        # H:172,A:135,B:109,C:137,S:157
        # エレブー
        poke_def = PokeStatic.create(Dexno.ELECTABUZZ, [Move.NIGHTSHADE])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 267)
        self.assertEqual(field.parties[1].get().hp, 172)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # ELECTABUZZ -> SNORLAX: ダメージ50
        self.assertEqual(field.parties[0].get().hp, 267 - 50)
        # SNORLAX -> ELECTABUZZ: ダメージ50*1.5-1=74
        self.assertEqual(field.parties[1].get().hp, 172 - 74)
