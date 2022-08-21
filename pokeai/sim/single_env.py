from typing import List, Optional, Tuple, Union
import numpy as np
from pokeai.sim.model import Party
from pokeai.sim.sim import Sim, SimExtraInfo, SimObservation

class ObservationConverter:
    def update(self, obs: SimObservation) -> None:
        """
        シミュレータの状態を与え、インスタンスの内部状態を更新する。
        以降のgetObservation, getReward, mapActionはこの内容に基づいて計算する。
        """
        raise NotImplementedError
    
    def getObservation(self) -> object:
        """
        独自の観測特徴量を出力する。
        バトル終了時でも、例外を生じず何らかの値を返す。
        """
        raise NotImplementedError
    
    def getReward(self) -> float:
        """
        報酬を出力する。学習のための補助的な報酬を含んでもよい。
        """
        raise NotImplementedError
    
    def mapAction(self, action: object) -> Optional[str]:
        """
        独自のactionから、シミュレータの行動(move1, switch2, ...)に変換する。
        行動選択ができないタイミングでは、Noneを返す。
        """
        raise NotImplementedError

class SingleEnv:
    """
    1つのシミュレータをラップし、2プレイヤー分の環境を提供するEnv
    """
    def __init__(self, parties: List[Party], observation_converters: List[ObservationConverter]) -> None:
        self.parties = parties
        self.observation_converters = observation_converters
        self.sim = None
        self.done = True
    
    def _convert_obs(self, obss: List[Tuple[SimObservation, SimExtraInfo]]):
        conv_obss = []
        infos = []
        for i in range(2):
            self.observation_converters[i].update(obss[i][0])
            conv_obss.append(self.observation_converters[i].getObservation())
            infos.append(obss[i][1])
        return conv_obss, infos
    
    def reset(self, return_info=False) -> Union[List[object], Tuple[List[object], List[SimExtraInfo]]]:
        self.sim = Sim()
        obs_with_infos = self.sim.start(self.parties)
        conv_obss, infos = self._convert_obs(obs_with_infos)
        self.done = False
        if return_info:
            return conv_obss, infos
        else:
            return conv_obss

    def step(self, actions: List[object]) -> Tuple[List[object], List[float], List[bool], List[object]]:
        if self.done:
            raise ValueError('step(): The battle has ended.')
        sim_actions = [self.observation_converters[i].mapAction(actions[i]) for i in range(2)]
        obs_with_infos = self.sim.step(sim_actions)
        conv_obss, infos = self._convert_obs(obs_with_infos)
        rewards = []
        dones = []
        if obs_with_infos[0][0].is_end:
            self.done = True
        for i in range(2):
            rewards.append(self.observation_converters[i].getReward())
            dones.append(obs_with_infos[i][0].is_end)
        return conv_obss, rewards, dones, infos
