"""
ゲーム中の乱数を生成
"""
import random
from enum import Enum, auto
import warnings


class GameRNGReason(Enum):
    MOVE_ORDER = auto()  # 先攻決め
    HIT = auto()  # 命中率
    DAMAGE = auto()  # ダメージのランダム変動
    CRITICAL = auto()  # 急所


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
    """

    def __init__(self):
        super().__init__()

    def _gen(self, player, reason, top) -> int:
        # TODO: player, reasonを条件として特定の値を与える機能
        if reason == GameRNGReason.HIT:
            # 必ず命中
            return 0
        if reason == GameRNGReason.DAMAGE:
            # ダメージは最大
            return top
        if reason == GameRNGReason.CRITICAL:
            # 急所に当たらない
            return top
        return 0
