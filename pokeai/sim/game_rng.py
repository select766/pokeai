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
