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


class TestMoveRazorwind(unittest.TestCase):
    """
    かまいたち
    """

    def test_basic(self):
        """
        かまいたち
        1ターン目は何もせず、次でダメージを与える
        あなをほると違い、敵の攻撃が当たる
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.BITE])
        # H:146,A:104,B:95,C:102,S:117
        poke_def = PokeStatic.create(Dexno.CHARMANDER, [Move.RAZORWIND])
        field = Field([Party([poke_atk]), Party([poke_def])])
        rng = GameRNGFixed()
        field.rng = rng
        field.rng.set_field(field)

        pk_b = field.parties[0].get()
        pk_c = field.parties[1].get()

        self.assertEqual(pk_b.hp, 152)
        self.assertEqual(pk_c.hp, 146)
        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDERが先に動き、ためる
        self.assertEqual(pk_b.hp, 152)
        # BULBASAUR -> CHARMANDER: ダメージ30
        self.assertEqual(pk_c.hp, 146 - 30)

        field.actions_begin = [FieldAction(FieldActionType.MOVE, move_idx=0),
                               FieldAction(FieldActionType.MOVE, move_idx=0)]
        self.assertEqual(field.step(), FieldPhase.BEGIN)

        # CHARMANDER -> BULBASAUR : ダメージ38
        self.assertEqual(pk_b.hp, 152 - 38)
        # BULBASAUR -> CHARMANDER: ダメージ30
        self.assertEqual(pk_c.hp, 146 - 30 * 2)
