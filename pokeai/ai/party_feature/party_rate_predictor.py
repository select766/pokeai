"""
パーティのレートを推定する回帰モジュール
"""
from typing import List
import numpy as np
from sklearn.preprocessing import StandardScaler
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
        feats_array = [self.feature_extractor.get_feature(party_t) for party_t in parties]
        return np.array(feats_array)

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
