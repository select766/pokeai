import numpy as np

from pokeai.ai.policy_model import PolicyModel


class LinearModel(PolicyModel):
    def __init__(self, feature_dims: int, action_dims: int):
        self.feature_dims = feature_dims
        self.action_dims = action_dims
        self.coef_ = np.zeros((feature_dims, action_dims), dtype=np.float)
        self.intercept_ = np.zeros((action_dims,), dtype=np.float)

    def __call__(self, feature: np.ndarray) -> np.ndarray:
        return feature @ self.coef_ + self.intercept_
