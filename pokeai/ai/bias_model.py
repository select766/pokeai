import numpy as np

from pokeai.ai.policy_model import PolicyModel


class BiasModel(PolicyModel):
    """
    単純に行動の選択確率にバイアスがかかったモデル
    状況にかかわらず有用な技を選ぶ確率を高めるだけの学習となり、比較対象として用いる
    """

    def __init__(self, feature_dims: int, action_dims: int):
        self.feature_dims = feature_dims
        self.action_dims = action_dims
        self.intercept_ = np.zeros((action_dims,), dtype=np.float)

    def __call__(self, feature: np.ndarray) -> np.ndarray:
        return self.intercept_
