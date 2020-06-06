import numpy as np
import torch

from pokeai.ai.generic_move_model.feature_extractor import FeatureExtractor


class Agent:
    def __init__(self, model: torch.nn.Module, feature_extractor: FeatureExtractor):
        self._model = model
        self._feature_extractor = feature_extractor

    def act(self, obs: object, reward: float) -> int:
        raise NotImplementedError

    def stop_episode(self, reward: float) -> None:
        raise NotImplementedError

    def _act_by_model(self, obs_vector, action_mask) -> int:
        # GPUを使うなら入力を.to(device)し、出力を.cpu().numpy()とする
        q_vector = self._model(torch.from_numpy(obs_vector[np.newaxis, ...])).numpy()[0]
        q_vector[action_mask == 0] = -np.inf
        action = int(np.argmax(q_vector))
        return action

    def _act_random(self, obs_vector, action_mask) -> int:
        actions = np.flatnonzero(action_mask)
        return int(np.random.choice(actions))
