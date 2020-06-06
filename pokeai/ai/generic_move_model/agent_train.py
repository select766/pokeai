import numpy as np

from pokeai.ai.generic_move_model.agent import Agent
from pokeai.ai.generic_move_model.feature_extractor import FeatureExtractor
from pokeai.ai.generic_move_model.replay_buffer import ReplayBuffer, ReplayBufferItem


class AgentTrain(Agent):
    def __init__(self, model, feature_extractor: FeatureExtractor, epsilon: float):
        """
        学習用エージェント
        :param model:
        :param feature_extractor:
        :param epsilon: ランダム行動の確率
        """
        super().__init__(model, feature_extractor)
        self._replay_buffer = ReplayBuffer(None)
        self._epsilon = epsilon
        self._last_state = None
        self._last_action_mask = None
        self._last_action = 0

    def act(self, obs: object, reward: float) -> int:
        obs_vector, action_mask = self._feature_extractor.transform(obs)
        if self._last_state is not None:
            self._replay_buffer.append(
                ReplayBufferItem(self._last_state, self._last_action_mask, self._last_action, obs_vector, action_mask,
                                 reward))
        if np.random.random() < self._epsilon:
            action = self._act_random(obs_vector, action_mask)
        else:
            action = self._act_by_model(obs_vector, action_mask)
        self._last_state = obs_vector
        self._last_action_mask = action_mask
        self._last_action = action
        return action

    def stop_episode(self, reward: float) -> None:
        self._replay_buffer.append(
            ReplayBufferItem(self._last_state, self._last_action_mask, self._last_action, None, None, reward))
        self._last_state = None
        self._last_action_mask = None
        self._last_action = 0
