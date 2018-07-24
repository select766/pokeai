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


class TestPokeChange(unittest.TestCase):
    """
    ポケモンの交代
    """

    def test_change(self):
        """
        交代。
        交代先に技が当たること、再度出した時にHPはそのまま、こんらんが治っていることを確認
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        pokest_0_0 = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.SWORDSDANCE])
        # H:162,A:102,B:97,C:187,S:172
        pokest_0_1 = PokeStatic.create(Dexno.ALAKAZAM, [Move.WATERGUN, Move.ROCKTHROW])
        # H:146,A:104,B:95,C:102,S:117
        pokest_1_0 = PokeStatic.create(Dexno.CHARMANDER, [Move.EMBER, Move.CONFUSERAY, Move.EARTHQUAKE])
        # H:267,A:162,B:117,C:117,S:82
        # カビゴン
        pokest_1_1 = PokeStatic.create(Dexno.SNORLAX, [Move.BODYSLAM])
        field = Field([Party([pokest_0_0, pokest_0_1]), Party([pokest_1_0, pokest_1_1])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ50、スリップダメージ152//16=9
        self.assertEqual(field.parties[0].get().hp, 152 - 50 - 9)
        # やけど
        # BULBASAUR -> CHARMANDER: ダメージ9(攻撃低下)
        self.assertEqual(field.parties[1].get().hp, 146 - 9)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.BURN)

        rng.enqueue_const(1, GameRNGReason.CONFUSE_TURN, 3)  # 3回混乱で自傷の可能性がある
        rng.enqueue_const(0, GameRNGReason.MOVE_CONFUSE, 1)  # 自傷せず
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=1)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        self.assertEqual(field.parties[0].get().hp, 152 - 50 - 9 - 9)
        self.assertEqual(field.parties[1].get().hp, 146 - 9)
        self.assertEqual(field.parties[0].get().v_confuse, True)

        field.actions_begin = [FieldAction(FieldActionType.CHANGE, change_idx=1),
                               FieldAction(FieldActionType.MOVE, move_idx=2)]
        # ALAKAZAMに交代
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        # CHARMANDER -> ALAKAZAM : ダメージ49
        self.assertEqual(field.parties[0].get().hp, 162 - 49)
        self.assertEqual(field.parties[1].get().hp, 146 - 9)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.EMPTY)
        self.assertEqual(field.parties[0].get().v_confuse, False)

        field.actions_begin = [FieldAction(FieldActionType.CHANGE, change_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=2)]
        # BULBASAURに交代
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        # CHARMANDER -> BULBASAUR : ダメージ46
        self.assertEqual(field.parties[0].get().hp, 152 - 50 - 9 - 9 - 46 - 9)
        self.assertEqual(field.parties[1].get().hp, 146 - 9)
        self.assertEqual(field.parties[0].get().nv_condition, PokeNVCondition.BURN)
        self.assertEqual(field.parties[0].get().v_confuse, False)

    def test_faint_change(self):
        """
        瀕死状態での交代
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        pokest_0_0 = PokeStatic.create(Dexno.BULBASAUR, [Move.TACKLE, Move.SWORDSDANCE])
        # H:162,A:102,B:97,C:187,S:172
        pokest_0_1 = PokeStatic.create(Dexno.ALAKAZAM, [Move.WATERGUN, Move.ROCKTHROW])
        # H:185,A:136,B:130,C:137,S:152
        pokest_1_0 = PokeStatic.create(Dexno.CHARIZARD, [Move.FIREBLAST, Move.CONFUSERAY, Move.EARTHQUAKE])
        # H:267,A:162,B:117,C:117,S:82
        # カビゴン
        pokest_1_1 = PokeStatic.create(Dexno.SNORLAX, [Move.BODYSLAM])
        field = Field([Party([pokest_0_0, pokest_0_1]), Party([pokest_1_0, pokest_1_1])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 185)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.FAINT_CHANGE)

        # CHARIZARD -> BULBASAUR : ダメージ188
        self.assertEqual(field.parties[0].get().hp, 0)
        # BULBASAUR -> CHARMANDER: 攻撃機会なし
        self.assertEqual(field.parties[1].get().hp, 185)

        field.actions_faint_change = [FieldAction(FieldActionType.FAINT_CHANGE, faint_change_idx=1),
                                      None]
        self.assertEqual(field.step(), FieldPhase.BEGIN)
        self.assertEqual(field.parties[0].get().hp, 162)
        self.assertEqual(field.parties[1].get().hp, 185)
