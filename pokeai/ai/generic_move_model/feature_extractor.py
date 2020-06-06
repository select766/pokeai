from typing import Tuple

import numpy as np

from pokeai.ai.common import get_possible_actions
from pokeai.ai.feature_extractor import FeatureExtractor as StateFeatureExtractor
from pokeai.ai.generic_move_model.choice_to_vec import ChoiceToVec
from pokeai.ai.rl_policy_observation import RLPolicyObservation


class FeatureExtractor:
    def __init__(self, party_size: int = 1):
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

    @property
    def output_dim(self):
        """
        出力次元数（行動数）
        :return:
        """
        # パーティがN匹の時、ポケモン1匹について技4つ、そのポケモンに通常交代・強制交代の6つ
        return 6 * self.party_size

    def transform(self, obs: RLPolicyObservation) -> Tuple[np.ndarray, np.ndarray]:
        """
        観測を特徴量ベクトルに変換
        :param obs:
        :return: 特徴量および合法手マスク
        """
        choice_idxs, choice_keys, choice_vec = get_possible_actions(obs.battle_status, obs.request)
        feat = np.zeros(self.input_shape, dtype=np.float32)
        # パーティ1匹の時のみ対応。交代対応の部分はダミーで埋められる。
        state_feat = self.state_feature_extractor.transform(obs.battle_status, choice_vec)
        feat[:len(state_feat), :] = state_feat[:, np.newaxis]
        feat[len(state_feat):, 0:4] = self.choice_to_vec.transform(obs.battle_status, obs.request)
        return feat, choice_vec
