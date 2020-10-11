from typing import Tuple

import numpy as np

from pokeai.ai.state_feature_extractor import StateFeatureExtractor
from pokeai.ai.generic_move_model.choice_to_vec import ChoiceToVec
from pokeai.ai.rl_policy_observation import RLPolicyObservation


class FeatureExtractor:
    def __init__(self, party_size: int):
        self.party_size = party_size
        self.state_feature_extractor = StateFeatureExtractor(feature_types=None, party_size=self.party_size)
        self.choice_to_vec = ChoiceToVec()

    @property
    def input_shape(self):
        """
        入力特徴量ベクトルの形状
        :return: 次元数のタプル
        """
        state_dims = self.state_feature_extractor.get_dims()
        choice_dims = self.choice_to_vec.get_dims()
        return (state_dims + choice_dims), self.output_dim

    def get_dim_meanings(self):
        return ["state/" + m for m in self.state_feature_extractor.get_dim_meanings()] + \
               ["choice/" + m for m in self.choice_to_vec.get_dim_meanings()]

    @property
    def output_dim(self) -> int:
        """
        出力次元数（最大行動数）
        :return:
        """
        # 技最大4つ＋今出てないポケモンに交代
        # 可能な行動数が少ない場合、無効なインデックスが生じる
        return 4 + self.party_size - 1

    def transform(self, obs: RLPolicyObservation) -> Tuple[np.ndarray, np.ndarray]:
        """
        観測を特徴量ベクトルに変換
        :param obs:
        :return: 特徴量(self.input_shape, float32)および合法手マスク((self.output_dim,), int32)
        """
        feat = np.zeros(self.input_shape, dtype=np.float32)
        state_feat = self.state_feature_extractor.transform(obs)
        feat[:len(state_feat), :] = state_feat[:, np.newaxis]
        feat[len(state_feat):, :len(obs.possible_actions)] = self.choice_to_vec.transform(obs)
        choice_vec = np.zeros((self.output_dim,), dtype=np.int32)
        choice_vec[:len(obs.possible_actions)] = 1
        return feat, choice_vec
