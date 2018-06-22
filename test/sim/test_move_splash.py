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


class TestMoveSplash(unittest.TestCase):
    """
    はねるがなにもしないことをテスト
    """

    def test_basic(self):
        """
        はねるがなにもしないことをテスト
        :return:
        """

        # H:152,A:101,B:101,C:117,S:97
        poke_atk = PokeStatic.create(Dexno.BULBASAUR, [Move.SPLASH])
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

        self.assertEqual(field.parties[0].get().hp, 152)
        self.assertEqual(field.parties[1].get().hp, 146)
