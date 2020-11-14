from typing import NamedTuple


class SurrogateRewardConfig(NamedTuple):
    hp_ratio: float
    alive_ratio: float


# 補助報酬を使用しない設定
SurrogateRewardConfigZero = SurrogateRewardConfig(hp_ratio=0.0, alive_ratio=0.0)
