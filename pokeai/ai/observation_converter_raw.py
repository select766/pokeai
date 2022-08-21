
from typing import Optional
from pokeai.sim.single_env import ObservationConverter
from pokeai.sim.sim import SimObservation


class ObservationConverterRaw(ObservationConverter):
    """
    生データを出力するObservationConverter
    """
    obs: SimObservation

    def update(self, obs: SimObservation) -> None:
        """
        シミュレータの状態を与え、インスタンスの内部状態を更新する。
        以降のgetObservation, getReward, mapActionはこの内容に基づいて計算する。
        """
        self.obs = obs
    
    def getObservation(self) -> SimObservation:
        """
        独自の観測特徴量を出力する。
        バトル終了時でも、例外を生じず何らかの値を返す。
        """
        return self.obs
    
    def getReward(self) -> float:
        """
        報酬を出力する。学習のための補助的な報酬を含んでもよい。
        """
        return 0.0
    
    def mapAction(self, action: str) -> Optional[str]:
        """
        独自のactionから、シミュレータの行動(move1, switch2, ...)に変換する。
        行動選択ができないタイミングでは、Noneを返す。
        """
        return action
