from collections import deque
import random
from typing import NamedTuple, Optional, List, Iterable
import numpy as np


class ReplayBufferItem(NamedTuple):
    state: np.ndarray
    action_mask: np.ndarray  # action数次元のnp.float32ベクトルで、合法手に1、それ以外に0を代入
    action: int  # 実際に選んだ行動
    next_state: Optional[np.ndarray]  # エピソード終端ではNone
    next_action_mask: Optional[np.ndarray]
    reward: float


class ReplayBuffer:
    def __init__(self, size: Optional[int]):
        self.buffer = deque(maxlen=size)

    def __len__(self):
        return len(self.buffer)

    def append(self, item: ReplayBufferItem):
        self.buffer.append(item)

    def extend(self, items: Iterable[ReplayBufferItem]):
        self.buffer.extend(items)

    def sample(self, size: int) -> List[ReplayBufferItem]:
        if len(self) < size:
            raise IndexError
        return random.sample(self.buffer, size)
