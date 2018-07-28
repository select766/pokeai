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


class TestMoveThrash(unittest.TestCase):
    """
    あばれる
    """

    def test_basic(self):
        """
        2ターン攻撃、その直後混乱
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        pokest_0_0 = PokeStatic.create(Dexno.BULBASAUR, [Move.THRASH])
        # H:162,A:102,B:97,C:187,S:172
        pokest_0_1 = PokeStatic.create(Dexno.ALAKAZAM, [Move.WATERGUN, Move.ROCKTHROW])
        # H:146,A:104,B:95,C:102,S:117
        pokest_1_0 = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.CONFUSERAY, Move.EARTHQUAKE])
        # ゴース
        pokest_1_1 = PokeStatic.create(Dexno.GASTLY, [Move.BODYSLAM])
        field = Field([Party([pokest_0_0, pokest_0_1]), Party([pokest_1_0, pokest_1_1])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 17)
        # BULBASAUR -> CHARMANDER: ダメージ44
        self.assertEqual(field.parties[1].get().hp, 146 - 44)
        self.assertEqual(field.parties[0].get().v_confuse, False)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ17
        self.assertEqual(field.parties[0].get().hp, 152 - 17 * 2)
        # BULBASAUR -> CHARMANDER: ダメージ44
        self.assertEqual(field.parties[1].get().hp, 146 - 44 * 2)
        self.assertEqual(field.parties[0].get().v_confuse, True)  # こんらんする

    def test_change_cancel(self):
        """
        最終でないターンで外れたら混乱せず終了
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        pokest_0_0 = PokeStatic.create(Dexno.BULBASAUR, [Move.THRASH, Move.WATERGUN])
        # H:162,A:102,B:97,C:187,S:172
        pokest_0_1 = PokeStatic.create(Dexno.ALAKAZAM, [Move.WATERGUN, Move.ROCKTHROW])
        # H:146,A:104,B:95,C:102,S:117
        pokest_1_0 = PokeStatic.create(Dexno.CHARMANDER, [Move.TACKLE, Move.CONFUSERAY, Move.EARTHQUAKE])
        # H:137,A:87,B:82,C:152,S:132
        # GASTLY ゴース
        pokest_1_1 = PokeStatic.create(Dexno.GASTLY, [Move.SPLASH])
        field = Field([Party([pokest_0_0, pokest_0_1]), Party([pokest_1_0, pokest_1_1])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.CHANGE, change_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 137)
        self.assertEqual(field.parties[0].get().v_confuse, False)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # 混乱せず攻撃できる
        # GASTLY -> BULBASAUR : ダメージ0
        self.assertEqual(field.parties[0].get().hp, 152)
        # BULBASAUR -> GASTLY: ダメージ15
        self.assertEqual(field.parties[1].get().hp, 137 - 15)
