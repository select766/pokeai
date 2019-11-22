import numpy as np
import copy


class PolicyModel:
    def __call__(self, feature: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def copy(self) -> "PolicyModel":
        return copy.deepcopy(self)
