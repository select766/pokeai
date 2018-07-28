"""
ゲーム中の乱数を生成
"""
import random
from collections import defaultdict
from enum import Enum, auto
import warnings
from typing import Dict, Tuple, List


class GameRNGReason(Enum):
    MOVE_ORDER = auto()  # 先攻決め
    HIT = auto()  # 命中率
    DAMAGE = auto()  # ダメージのランダム変動
    CRITICAL = auto()  # 急所
    SIDE_EFFECT = auto()  # 追加効果
    MOVE_PARALYSIS = auto()  # まひ状態での行動
    MOVE_CONFUSE = auto()  # 混乱状態での行動
    SLEEP_TURN = auto()  # ねむるターン数
    CONFUSE_TURN = auto()  # 混乱ターン数
    PSYWAVE = auto()  # サイコウェーブのダメージ
    THRASH = auto()  # あばれるターン数
    BARRAGE = auto()  # たまなげ連続回数(0~7で、0,1,2=2回、3,4,5=3回、6=4回、7=5回)


class GameRNG:
    field: object

    def __init__(self):
        self.field = None

    def set_field(self, field):
        self.field = field

    def _gen(self, player, reason, top) -> int:
        raise NotImplementedError

    def gen(self, player, reason, top=255):
        val = self._gen(player, reason, top)
        if self.field is None:
            warnings.warn("RNG field is not set")
        # TODO: ログに記録
        return val


class GameRNGRandom(GameRNG):
    _rng: random.Random

    def __init__(self, seed=None):
        super().__init__()
        self._rng = random.Random(seed)

    def _gen(self, player, reason, top) -> int:
        return self._rng.randint(0, top)


class GameRNGFixed(GameRNG):
    """
    テスト用に固定乱数を与える。
    特定用途の乱数が取得されるときにユーザ指定の値を返す機能を有する。
    """

    const_store: Dict[Tuple[int, GameRNGReason], List[int]]

    def __init__(self):
        super().__init__()
        self.const_store = defaultdict(list)

    def _gen(self, player, reason, top) -> int:
        const_list = self.const_store[(player, reason)]
        if len(const_list) > 0:
            return const_list.pop()
        if reason == GameRNGReason.HIT:
            # 必ず命中
            return 0
        if reason == GameRNGReason.DAMAGE:
            # ダメージは最大
            return top
        if reason == GameRNGReason.CRITICAL:
            # 急所に当たらない
            return top
        if reason == GameRNGReason.SIDE_EFFECT:
            # 追加効果発生
            return 0
        if reason == GameRNGReason.MOVE_PARALYSIS:
            # まひで行動不能
            return 0
        if reason == GameRNGReason.MOVE_CONFUSE:
            # こんらんで自滅
            return 0
        if reason == GameRNGReason.CONFUSE_TURN:
            # こんらんターン数=最小=すぐ解ける
            return 0
        if reason == GameRNGReason.SLEEP_TURN:
            # 眠るターン数=最小
            return 0
        if reason == GameRNGReason.PSYWAVE:
            # サイコウェーブダメージ=最大
            return top
        if reason == GameRNGReason.THRASH:
            # あばれるターン数=最小
            return 0
        if reason == GameRNGReason.BARRAGE:
            # たまなげ連続回数=最小
            return 0
        return 0

    def enqueue_const(self, player: int, reason: GameRNGReason, value: int) -> None:
        """
        特定条件で次に呼び出されたときに返す定数を設定する。
        同条件に対してはキューとしてふるまう。
        :param player:
        :param reason:
        :param value:
        :return:
        """
        self.const_store[(player, reason)].append(value)

    def is_const_empty(self) -> bool:
        """
        定数がすべて消費されているかを得る。
        :return:
        """
        for k, v in self.const_store.items():
            if len(v) > 0:
                return False
        return True
