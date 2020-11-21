from typing import NamedTuple


class SurrogateRewardConfig(NamedTuple):
    hp_ratio: float
    alive_ratio: float
    """
    敵側のHP率などだけを補助報酬として使う
    """
    only_opponent: bool
    """
    ゲーム終了時に、今まで与えた補助報酬をキャンセルする（補助報酬の和をゲームの勝敗の報酬から引く）
    """
    offset_at_end: bool


SurrogateRewardConfigDefaults = {"hp_ratio": 0.0, "alive_ratio": 0.0, "only_opponent": False, "offset_at_end": False}

# 補助報酬を使用しない設定
SurrogateRewardConfigZero = SurrogateRewardConfig(**SurrogateRewardConfigDefaults)
