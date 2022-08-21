from typing import Callable, Iterable, Iterator, List, NamedTuple, Tuple, Union
from pokeai.sim.model import Party
from pokeai.sim.sim import SimExtraInfo
from pokeai.sim.single_env import ObservationConverter, SingleEnv

class TrainEnv:
    """
    学習用のenv。複数のシミュレータを同時に実行し、バトルが終了したら直ちに次のバトルが開始する。
    """

    n_envs: int
    n_obss: int
    envs: List[SingleEnv]
    _party_pair_iterator: Iterator[List[Party]]
    _observation_converter_factory: Callable[[], ObservationConverter]

    def __init__(self, n_envs: int, party_pair_generator: Iterable[List[Party]], observation_converter_factory: Callable[[], ObservationConverter]) -> None:
        self.n_envs = n_envs
        self.n_obss = n_envs * 2
        self._party_pair_iterator = iter(party_pair_generator)
        self._observation_converter_factory = observation_converter_factory
    
    def reset(self, return_info=False) -> Union[List[object], Tuple[List[object], List[SimExtraInfo]]]:
        self.envs = []
        all_obss = []
        all_infos = []
        
        for _ in range(self.n_envs):
            env = self._start_new_env()
            obss, infos = env.reset(return_info=True)
            all_obss.extend(obss)
            all_infos.extend(infos)
            self.envs.append(env)
        
        if return_info:
            return all_obss, all_infos
        else:
            return all_obss
    
    def _start_new_env(self) -> SingleEnv:
        party_pair = next(self._party_pair_iterator)
        env = SingleEnv(party_pair, [self._observation_converter_factory(), self._observation_converter_factory()])
        return env

    def step(self, actions: List[object]) -> Tuple[List[object], List[float], List[bool], List[SimExtraInfo]]:
        assert len(actions) == self.n_obss
        all_obss = []
        all_rewards = []
        all_infos = []
        all_dones = []
        for i in range(self.n_envs):
            env = self.envs[i]
            obss, rewards, dones, infos = env.step([actions[i*2], actions[i*2+1]])
            if dones[0]:
                # envs[i]が終了したので新しいEnvで差し替える。
                # 終了時の報酬（勝敗）は終了したEnvのものをそのまま返す。
                # 終了時の観測はinfoのterminal_observationに与える。
                new_env = self._start_new_env()
                terminal_obss = obss
                obss, infos = new_env.reset(return_info=True)
                infos = [infos[player]._replace(terminal_observation=terminal_obss[player]) for player in range(2)]
                self.envs[i] = new_env
            all_obss.extend(obss)
            all_rewards.extend(rewards)
            all_infos.extend(infos)
            all_dones.extend(dones)
        return all_obss, all_rewards, all_dones, all_infos

class TrainSideStaticEnvBattleConfiguration(NamedTuple):
    """
    バトル1回で用いるパーティ、ポリシー固定側のObservationConverterおよびpolicy
    """
    party_pair: List[Party]
    static_observation_converter: ObservationConverter
    static_policy: Callable[[object], object] # obs -> action

class TrainSideStaticEnv:
    """
    学習用のenv。複数のシミュレータを同時に実行し、バトルが終了したら直ちに次のバトルが開始する。プレイヤー2に固定のポリシーを用い、プレイヤー1のみの観測を返す。
    """

    n_envs: int
    n_obss: int
    envs: List[SingleEnv]
    _env_battle_configurations: List[TrainSideStaticEnvBattleConfiguration]
    _env_static_pending_actions: List[object]
    battle_configuration_iterator: Iterator[TrainSideStaticEnvBattleConfiguration]
    _observation_converter_factory: Callable[[], ObservationConverter]

    def __init__(self, n_envs: int, battle_configuration_generator: Iterable[TrainSideStaticEnvBattleConfiguration], observation_converter_factory: Callable[[], ObservationConverter]) -> None:
        self.n_envs = n_envs
        self.n_obss = n_envs
        self.battle_configuration_iterator = iter(battle_configuration_generator)
        self._observation_converter_factory = observation_converter_factory
    
    def reset(self, return_info=False) -> Union[List[object], Tuple[List[object], List[SimExtraInfo]]]:
        self.envs = []
        self._env_battle_configurations = []
        self._env_static_pending_actions = []
        all_obss = []
        all_infos = []
        
        for _ in range(self.n_envs):
            env, battle_config = self._start_new_env()
            obss, infos = env.reset(return_info=True)
            all_obss.append(obss[0])
            all_infos.append(infos[0])
            static_action = battle_config.static_policy(obss[1])
            self._env_static_pending_actions.append(static_action)
            self.envs.append(env)
            self._env_battle_configurations.append(battle_config)
        
        if return_info:
            return all_obss, all_infos
        else:
            return all_obss
    
    def _start_new_env(self) -> Tuple[SingleEnv, TrainSideStaticEnvBattleConfiguration]:
        battle_config = next(self.battle_configuration_iterator)
        env = SingleEnv(battle_config.party_pair, [self._observation_converter_factory(), battle_config.static_observation_converter])
        return env, battle_config

    def step(self, actions: List[object]) -> Tuple[List[object], List[float], List[bool], List[SimExtraInfo]]:
        assert len(actions) == self.n_obss
        all_obss = []
        all_rewards = []
        all_infos = []
        all_dones = []
        for i in range(self.n_envs):
            env = self.envs[i]
            obss, rewards, dones, infos = env.step([actions[i], self._env_static_pending_actions[i]])
            if dones[0]:
                # envs[i]が終了したので新しいEnvで差し替える。
                # 終了時の報酬（勝敗）は終了したEnvのものをそのまま返す。
                # 終了時の観測はinfoのterminal_observationに与える。
                new_env, new_battle_config = self._start_new_env()
                terminal_obss = obss
                obss, infos = new_env.reset(return_info=True)
                infos = [infos[player]._replace(terminal_observation=terminal_obss[player]) for player in range(2)]
                self.envs[i] = new_env
                self._env_battle_configurations[i] = new_battle_config
            all_dones.append(dones[0])
            all_obss.append(obss[0])
            all_rewards.append(rewards[0])
            all_infos.append(infos[0])
            self._env_static_pending_actions[i] = self._env_battle_configurations[i].static_policy(obss[1])
        return all_obss, all_rewards, all_dones, all_infos
