import numpy as np


class PolicyModel:
    def __call__(self, feature: np.ndarray) -> np.ndarray:
        raise NotImplementedError
