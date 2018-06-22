import unittest

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType


class TestPokeStatic(unittest.TestCase):
    def test_status(self):
        """
        パラメータ計算が正しいか
        :return:
        """
        pokest = PokeStatic.create(Dexno.BULBASAUR, [Move.BITE])
        self.assertEqual(pokest.dexno, Dexno.BULBASAUR)
        self.assertEqual(pokest.moves, [Move.BITE])
        self.assertEqual(pokest.poke_types, [PokeType.GRASS, PokeType.POISON])
        self.assertEqual(pokest.lv, 50)  # デフォルトレベル50
        self.assertEqual(pokest.max_hp, 152)  # デフォルトでは理想個体（個体値努力値MAX）
        self.assertEqual(pokest.st_a, 101)
        self.assertEqual(pokest.st_b, 101)
        self.assertEqual(pokest.st_c, 117)
        self.assertEqual(pokest.st_s, 97)

        pokest = PokeStatic.create(Dexno.CHARMANDER, [Move.FLAMETHROWER, Move.THUNDERWAVE], lv=30)
        self.assertEqual(pokest.dexno, Dexno.CHARMANDER)
        self.assertEqual(pokest.moves, [Move.FLAMETHROWER, Move.THUNDERWAVE])
        self.assertEqual(pokest.poke_types, [PokeType.FIRE])
        self.assertEqual(pokest.lv, 30)
        self.assertEqual(pokest.max_hp, 91)
        self.assertEqual(pokest.st_a, 64)
        self.assertEqual(pokest.st_b, 59)
        self.assertEqual(pokest.st_c, 63)
        self.assertEqual(pokest.st_s, 72)
