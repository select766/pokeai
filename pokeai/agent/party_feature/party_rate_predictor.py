"""
パーティのレートを推定する回帰モジュール
"""
from typing import List
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVR

from pokeai.agent.party_feature.party_feature_extractor import PartyFeatureExtractor
from pokeai.sim.party_template import PartyTemplate


class PartyRatePredictor:
    def __init__(self, params):
        self.params = params
        self.feature_extractor = PartyFeatureExtractor(**self.params["feature_params"])
        self.regressor = LinearSVR(**self.params["regressor_params"])
        self.scaler = StandardScaler()

    def _extract_feats(self, parties: List[PartyTemplate]):
        feats_array = [self.feature_extractor.get_feature(party_t) for party_t in parties]
        return np.array(feats_array)

    def fit(self, X: List[PartyTemplate], y: List[float]):
        feats = self._extract_feats(X)
        # レートが1500中心だと大きすぎるのでスケーリングする
        scaled_rates = self.scaler.fit_transform(np.array(y)[:, np.newaxis])[:, 0]
        self.regressor.fit(feats, scaled_rates)

    def score(self, X: List[PartyTemplate], y: List[float]) -> float:
        feats = self._extract_feats(X)
        scaled_rates = self.scaler.transform(np.array(y)[:, np.newaxis])[:, 0]
        return self.regressor.score(feats, scaled_rates)

    def predict(self, X: List[PartyTemplate]) -> List[float]:
        feats = self._extract_feats(X)
        scaled_rates = self.regressor.predict(feats)
        rates = self.scaler.inverse_transform(np.array(scaled_rates)[:, np.newaxis])[:, 0]
        return rates.tolist()
