"""
パーティのレートを推定する回帰モジュール
"""
from typing import List
import numpy as np
import scipy.sparse
from sklearn.svm import LinearSVR

from pokeai.ai.party_feature.party_feature_extractor import PartyFeatureExtractor
from pokeai.sim.party_generator import Party


class PartyRatePredictor:
    SCALE_BIAS = 1500.0
    SCALE_STD = 200.0

    def __init__(self, params):
        self.params = params
        self.feature_extractor = PartyFeatureExtractor(**self.params["feature_params"])
        self.regressor = LinearSVR(**self.params["regressor_params"])

    def _extract_feats(self, parties: List[Party]):
        # scipy.sparse.csr_matrixは1次元ベクトルを渡すと(1, len)サイズの2次元行列になる
        # LinearSVRではfloat64, CSR形式が受け付けられる
        # https://github.com/scikit-learn/scikit-learn/blob/14031f65d144e3966113d3daec836e443c6d7a5b/sklearn/svm/classes.py#L374
        feats_array = [scipy.sparse.csr_matrix(self.feature_extractor.get_feature(party_t).astype(np.float))
                       for party_t in parties]
        return scipy.sparse.vstack(feats_array, format='csr')

    def _scale(self, y: np.ndarray):
        return (y - PartyRatePredictor.SCALE_BIAS) / PartyRatePredictor.SCALE_STD

    def _inverse_scale(self, y: np.ndarray):
        return y * PartyRatePredictor.SCALE_STD + PartyRatePredictor.SCALE_BIAS

    def fit(self, X: List[Party], y: List[float]):
        feats = self._extract_feats(X)
        # レートが1500中心だと大きすぎるのでスケーリングする
        scaled_rates = self._scale(np.array(y))
        self.regressor.fit(feats, scaled_rates)

    def score(self, X: List[Party], y: List[float]) -> float:
        feats = self._extract_feats(X)
        scaled_rates = self._scale(np.array(y))
        return self.regressor.score(feats, scaled_rates)

    def predict(self, X: List[Party]) -> List[float]:
        feats = self._extract_feats(X)
        scaled_rates = self.regressor.predict(feats)
        rates = self._inverse_scale(np.array(scaled_rates))
        return rates.tolist()
