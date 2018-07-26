import unittest

from pokeai.sim.dexno import Dexno
from pokeai.sim.move import Move
from pokeai.agent.party_generator import PossiblePokeDB

ppdb = None  # type: PossiblePokeDB


class TestPossiblePokeDB(unittest.TestCase):
    """
    ポケモンの覚える技が正しいかチェック
    """

    def test_evol_none(self):
        """
        進化しないポケモン
        :return:
        """
        ms = ppdb.get_leanable_moves(Dexno.LICKITUNG, 25)
        self.assertIn(Move.STOMP, ms)
        self.assertIn(Move.SURF, ms)
        self.assertNotIn(Move.SLAM, ms)  # レベル不足

        # 伝説不可
        ms = ppdb.get_leanable_moves(Dexno.MEWTWO, 100)
        self.assertTrue(len(ms) == 0)
        ms = ppdb.get_leanable_moves(Dexno.MEW, 100)
        self.assertTrue(len(ms) == 0)

    def test_evol_stone(self):
        """
        最後が石進化
        :return:
        """
        ms = ppdb.get_leanable_moves(Dexno.EXEGGUTOR, 32)  # 石進化
        self.assertIn(Move.STUNSPORE, ms)  # タマタマLV32が覚える
        self.assertNotIn(Move.POISONPOWDER, ms)  # タマタマLV37が覚える
        self.assertIn(Move.SOLARBEAM, ms)  # 技マシン

        # ニョロモ→ニョロゾ LV25、ニョロボン 石進化
        # ニョロゾが野生LV15で手に入る
        ms = ppdb.get_leanable_moves(Dexno.POLIWRATH, 14)
        self.assertTrue(len(ms) == 0)
        ms = ppdb.get_leanable_moves(Dexno.POLIWRATH, 15)
        self.assertTrue(len(ms) > 0)
        ms = ppdb.get_leanable_moves(Dexno.POLIWRATH, 44)
        self.assertNotIn(Move.HYDROPUMP, ms)  # ニョロモLV45が覚える
        ms = ppdb.get_leanable_moves(Dexno.POLIWRATH, 45)
        self.assertIn(Move.HYDROPUMP, ms)  # ニョロモLV45が覚える

    def test_evol_lv(self):
        """
        レベル進化
        :return:
        """
        # フシギバナ 進化LV32
        ms = ppdb.get_leanable_moves(Dexno.VENUSAUR, 31)
        self.assertTrue(len(ms) == 0)
        ms = ppdb.get_leanable_moves(Dexno.VENUSAUR, 32)
        self.assertTrue(len(ms) > 0)
        # フシギダネがLV41で覚えられるねむりごなは、最速で進化させてもLV42にならないと無理
        ms = ppdb.get_leanable_moves(Dexno.VENUSAUR, 41)
        self.assertNotIn(Move.SLEEPPOWDER, ms)
        ms = ppdb.get_leanable_moves(Dexno.VENUSAUR, 42)
        self.assertIn(Move.SLEEPPOWDER, ms)

        ms = ppdb.get_leanable_moves(Dexno.IVYSAUR, 32)
        self.assertNotIn(Move.HYPERBEAM, ms)  # 最終進化限定

        # ミニリュウ→ハクリュー LV30→カイリュー LV55
        ms = ppdb.get_leanable_moves(Dexno.DRATINI, 49)  # ミニリュウ
        self.assertNotIn(Move.HYPERBEAM, ms)  # 技マシンでは覚えない
        ms = ppdb.get_leanable_moves(Dexno.DRATINI, 50)  # ミニリュウ
        self.assertIn(Move.HYPERBEAM, ms)  # LV50で覚える

        # ビリリダマ→マルマインLV30
        # しかし、マルマインがゲーム内交換でLV3で入手可能
        ms = ppdb.get_leanable_moves(Dexno.VOLTORB, 3)  # ビリリダマ
        self.assertTrue(len(ms) == 0)
        ms = ppdb.get_leanable_moves(Dexno.ELECTRODE, 3)  # マルマイン
        self.assertTrue(len(ms) > 0)

        # ビードル→コクーンLV7→スピアーLV10
        # コクーンLV4が野生入手可能だが、どくばりは進化前限定
        ms = ppdb.get_leanable_moves(Dexno.WEEDLE, 3)
        self.assertIn(Move.POISONSTING, ms)
        ms = ppdb.get_leanable_moves(Dexno.KAKUNA, 4)
        self.assertNotIn(Move.POISONSTING, ms)
        ms = ppdb.get_leanable_moves(Dexno.KAKUNA, 7)
        self.assertIn(Move.POISONSTING, ms)

        # スプーン曲げは野生ユンゲラーLV20しか覚えておらず、LV16で進化した個体は覚えられないはず
        # この事態はまだ考慮していない
        # ms = ppdb.get_leanable_moves(Dexno.KADABRA, 16)  # LV16
        # self.assertNotIn(Move.KINESIS, ms)


def setUpModule():
    # デフォルトのdb
    global ppdb
    ppdb = PossiblePokeDB(allow_rare=False)
