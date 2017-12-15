# -*- coding:utf-8 -*-

from logging import getLogger
from abc import ABCMeta, abstractmethod
from typing import List

import numpy as np
import gym
import gym.spaces
import pokeai.sim as sim

logger = getLogger(__name__)

N_POKEMON_SPECIES = 9
N_MOVES = 20


class RewardConfig:
    """
    報酬の設定
    """
    reward_win: float
    reward_draw: float
    reward_invalid: float
    reward_damage_friend: float
    reward_damage_enemy: float

    def __init__(self, reward_win=1.0, reward_draw=0.0, reward_invalid=-10.0, reward_damage_friend=0.0,
                 reward_damage_enemy=0.0):
        """
        報酬の設定
        :param reward_win: 勝利時にもらえる報酬。敗北時は-reward_winの報酬。
        :param reward_draw: 引き分け時（一定ターン数以上経過時）にもらえる報酬。
        :param reward_invalid: その局面で選べない行動を選んだ場合の報酬。通常負の値を指定する。
        :param reward_damage_friend: 味方ポケモンのダメージに対する報酬。(-reward_damage_friend * ダメージ / 1024)の報酬。
        :param reward_damage_enemy: 敵ポケモンのダメージに対する報酬。(reward_damage_enemy * ダメージ / 1024)の報酬。
        """
        self.reward_win = reward_win
        self.reward_draw = reward_draw
        self.reward_invalid = reward_invalid
        self.reward_damage_friend = reward_damage_friend
        self.reward_damage_enemy = reward_damage_enemy


class EnvRule:
    """
    環境レベルでの対戦ルール設定
    """
    party_size: int
    faint_change_random: bool

    def __init__(self, party_size: int = 3, faint_change_random: bool = False):
        """
        環境レベルでの対戦ルール設定
        :param party_size: パーティのポケモン数
        :param faint_change_random: 瀕死になったポケモンの交代をランダムに行うか、エージェントが行うか
        """
        self.party_size = party_size
        self.faint_change_random = faint_change_random


def get_one_hot_list(idx: int, list_len: int) -> List[int]:
    vec = [0] * list_len
    vec[idx] = 1
    return vec


def get_one_hot_vector(idx: int, vec_len: int) -> np.ndarray:
    vec = np.zeros((vec_len,), dtype=np.float32)
    vec[idx] = 1.0
    return vec


class Observer(metaclass=ABCMeta):
    """
    観測ベクトル生成クラスの基底クラス
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def get_entry_names(self, env: "PokeaiEnv") -> List[str]:
        """
        観測ベクトルの各次元の名称を返す。
        :return:
        """
        pass

    @abstractmethod
    def get_obs_size(self, env: "PokeaiEnv") -> int:
        """
        観測ベクトルの長さを取得する。
        :return:
        """
        pass

    @abstractmethod
    def observe(self, env: "PokeaiEnv", player: int) -> np.ndarray:
        """
        観測ベクトルを計算する。
        :param env:
        :param player: 観測されるプレイヤー。
        :return:
        """
        raise NotImplementedError


class ObserverPossibleAction(Observer):
    """
    可能な行動を表す状態を観測するクラス
    """

    def __init__(self):
        pass

    def get_entry_names(self, env: "PokeaiEnv"):
        names = []
        for move_id in range(N_MOVES):
            names.append(f"move_{move_id}")
        for poke_idx in range(env.env_rule.party_size):
            names.append(f"change_to_{poke_idx}")
        for poke_idx in range(env.env_rule.party_size):
            names.append(f"faint_change_to_{poke_idx}")
        return names

    def get_obs_size(self, env: "PokeaiEnv"):
        return N_MOVES + env.env_rule.party_size * 2

    def observe(self, env: "PokeaiEnv", player: int):
        return env.get_possible_action_vec(player)


class ObserverFightingPoke(Observer):
    """
    場に出ているポケモンの状態を観測するクラス
    """

    def __init__(self, from_enemy: bool, nv_condition: bool, v_condition: bool, rank: bool):
        self.from_enemy = from_enemy
        self.nv_condition = nv_condition
        # 以下未実装
        assert v_condition is False
        assert rank is False
        self.v_condition = v_condition
        self.rank = rank

    def get_entry_names(self, env: "PokeaiEnv"):
        names = []
        for species in range(N_POKEMON_SPECIES):
            names.append(f"species_{species}")
        for move_id in range(N_MOVES):
            names.append(f"move_{move_id}")
        names.append("is_alive")
        names.append("hp")
        names.append("max_hp")
        if self.nv_condition:
            names.extend(["nv_empty", "nv_poison", "nv_paralysis", "nv_burn", "nv_sleep", "nv_freeze"])

    def get_obs_size(self, env: "PokeaiEnv"):
        size = 0
        size += N_POKEMON_SPECIES
        size += N_MOVES
        size += 3
        if self.nv_condition:
            size += 6
        return size

    def observe(self, env: "PokeaiEnv", player: int):
        target_player = 1 - player if self.from_enemy else player
        party = env.field.parties[target_player]
        poke = party.get_fighting_poke()

        vecs = []
        vecs.append(get_one_hot_vector(poke.static_param.dexno.value - 1, N_POKEMON_SPECIES))
        move_vec = np.zeros((N_MOVES,), dtype=np.float32)
        for move_id in poke.static_param.move_ids:
            move_vec[move_id.value - 1] = 1
        vecs.append(move_vec)
        vecs.append([int(not poke.is_faint), poke.hp / 1024.0, poke.static_param.max_hp / 1024.0])
        if self.nv_condition:
            vecs.append(get_one_hot_vector(poke.nv_condition.value - sim.PokeNVCondition.Empty.value, 6))
        # vec[ofs + 9] = int(poke.confusion_turn > 0)
        # vec[ofs + 10] = int(poke.bad_poison)
        # vec[ofs + 11] = min(poke.bad_poison_turn / 16.0, 1.0)
        # vec[ofs + 12] = int(poke.reflect)
        # vec[ofs + 13] = int(poke.digging)
        # vec[ofs + 14] = poke.rank_a / 12.0 + 0.5
        # vec[ofs + 15] = poke.rank_b / 12.0 + 0.5
        # vec[ofs + 16] = poke.rank_c / 12.0 + 0.5
        # vec[ofs + 17] = poke.rank_s / 12.0 + 0.5
        # vec[ofs + 18] = poke.rank_accuracy / 12.0 + 0.5
        # vec[ofs + 19] = poke.rank_evasion / 12.0 + 0.5
        return np.concatenate(vecs).astype(np.float32)


class PokeaiEnv(gym.Env):
    def __init__(self, env_rule: EnvRule, reward_config: RewardConfig, initial_seed, party_generator,
                 observers: List[Observer], enemy_agent=None):
        self.env_rule = env_rule
        self.party_generator = party_generator
        self.seed = initial_seed
        self.reward_config = reward_config
        self.observers = observers
        self.enemy_agent = enemy_agent
        self.action_space = gym.spaces.Discrete(N_MOVES + env_rule.party_size * 2)  # 技、交代先、ひんし交代先
        self.observation_len = sum(observer.get_obs_size(self) for observer in observers)
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=(self.observation_len,))

    def _reset(self):
        """
        環境をリセットする。パーティは新たに生成される。
        :return:
        """
        parties = self.party_generator()
        assert self.env_rule.party_size == len(parties[0].pokes) and self.env_rule.party_size == len(parties[1].pokes)
        self.field = sim.Field(parties)
        self.field.rng = sim.BattleRngRandom(seed=self.seed)
        self.seed += 1
        self.field.logger = sim.FieldLoggerBuffer()
        self.friend_player = 0
        self.enemy_player = 1 - self.friend_player
        self.last_hp_eval_score = self._calc_hp_eval_score(self.friend_player)
        self.game_end = False
        self.result_win = False
        self.result_draw = False
        return self.make_observation()

    def get_possible_action_vec(self, player):
        """
        現在可能な行動を表すベクトルを取得する。
        :param player:
        :return: np.ndarray(float32)、可能なら1、不可能なら0。
        """
        party_size = self.env_rule.party_size
        vec = np.zeros((N_MOVES + party_size * 2), dtype=np.float32)
        party = self.field.parties[player]
        living_bench_pokes = [int(not poke.is_faint) for poke in party.pokes]
        living_bench_pokes[party.fighting_poke_idx] = 0

        if self.field.phase is sim.FieldPhase.Begin:
            # 技・交代選択
            f_poke = party.get_fighting_poke()
            if f_poke.move_handler is not None:
                # 連続技発動中なので、それしか選べない
                move_id = f_poke.move_handler.move_entry.move_id
                vec[move_id.value - 1] = 1
            else:
                # すべての技+生きている控え
                for move_id in f_poke.static_param.move_ids:
                    vec[move_id.value - 1] = 1
                vec[N_MOVES:N_MOVES + party_size] = living_bench_pokes
        elif self.field.phase is sim.FieldPhase.FaintChange:
            # ひんしによる交代選択
            vec[N_MOVES + party_size:] = living_bench_pokes
        return vec

    def _calc_total_hp(self, party):
        hp_sum = 0
        for poke in party.pokes:
            hp_sum += poke.hp
        return hp_sum

    def _calc_hp_eval_score(self, friend_player):
        """
        friend playerからみた体力量の差の評価値
        """
        hp_diff = self._calc_total_hp(self.field.parties[friend_player]) * self.reward_config.reward_damage_friend \
                  - self._calc_total_hp(self.field.parties[1 - friend_player]) * self.reward_config.reward_damage_enemy
        hp_score = hp_diff / 1024.0
        return hp_score

    def make_observation(self, from_enemy=False):
        # 敵から見た場合の特徴も得られる構造。敵エージェントの行動決定に用いる。
        friend_player = self.friend_player if not from_enemy else self.enemy_player
        vectors = [observer.observe(self, friend_player) for observer in self.observers]
        return np.concatenate(vectors).astype(np.float32)

    def correct_action(self, player, action):
        """
        現在可能な行動かどうかを判定し、不正な行動であればランダムに可能な行動に置き換える
        (actionが可能な行動かどうか, 補正された行動)を返す。
        actionがNoneの場合、可能な範囲のランダムな行動を返す。
        """
        possible_action_vec = self.get_possible_action_vec(player)
        if action is not None and possible_action_vec[action] != 0:
            # OK
            return True, action
        else:
            # だめなのでランダム選択
            return False, np.random.choice(np.flatnonzero(possible_action_vec))

    def random_action_func(self):
        _, action = self.correct_action(self.friend_player, None)
        return action

    def _action_to_field_action(self, player, action):
        """
        整数であらわされた行動を行動オブジェクトに変換する
        :param player:
        :param action:
        :return:
        """
        if action < N_MOVES:
            move_idx = self.field._get_fighting_poke(player).static_param.move_ids.index(sim.MoveID(action + 1))
            assert move_idx >= 0
            return sim.FieldActionBegin.move(move_idx)
        elif action < N_MOVES + self.env_rule.party_size:
            return sim.FieldActionBegin.change(action - N_MOVES)
        else:
            return sim.FieldActionFaintChange(action - (N_MOVES + self.env_rule.party_size))

    def _sample_enemy_action(self):
        if self.enemy_agent is not None:
            # 敵モデルで最善の行動をとる
            enemy_action = self.enemy_agent.act(self.make_observation(from_enemy=True))
        else:
            # ランダムプレイヤー
            enemy_action = None
            # TODO: 今は交代を選ばないようにしているが、学習がうまくいくようになれば解除
            possible_action_vec = self.get_possible_action_vec(self.enemy_player)
            possible_action_vec[N_MOVES:N_MOVES + self.env_rule.party_size] = 0  # 交代を選ばない
            enemy_action = np.random.choice(np.flatnonzero(possible_action_vec))
        # 敵モデルが不正な行動を取る可能性もあるので訂正しておく
        _, enemy_corrected_action = self.correct_action(self.enemy_player, enemy_action)
        enemy_fa = self._action_to_field_action(self.enemy_player, enemy_corrected_action)
        return enemy_fa

    def _step(self, action):
        # action: int 0 to 3 which represents move index
        assert not self.game_end
        enemy_action_needed = False
        if self.field.phase is sim.FieldPhase.Begin:
            # 技または交代
            action_valid, corrected_action = self.correct_action(self.friend_player, action)
            friend_fa = self._action_to_field_action(self.friend_player, corrected_action)
            enemy_action_needed = True

        elif self.field.phase is sim.FieldPhase.FaintChange:
            # ひんし交代
            # プレイヤーがひんしになっているときのみ
            action_valid, corrected_action = self.correct_action(self.friend_player, action)
            friend_fa = self._action_to_field_action(self.friend_player, corrected_action)
            if self.field.parties[self.enemy_player].get_fighting_poke().is_faint:
                # 敵側もひんしなので、交代の行動選択
                enemy_action_needed = True

        if enemy_action_needed:
            enemy_fa = self._sample_enemy_action()
        else:
            enemy_fa = None

        if self.friend_player == 0:
            fa_list = [friend_fa, enemy_fa]
        else:
            fa_list = [enemy_fa, friend_fa]

        if self.field.phase is sim.FieldPhase.Begin:
            self.field.set_actions_begin(fa_list)
        elif self.field.phase is sim.FieldPhase.FaintChange:
            self.field.set_actions_faint_change(fa_list)

        while True:
            next_phase = self.field.step()
            if next_phase is sim.FieldPhase.FaintChange:
                # 敵側のみが交代であれば、自動で選択してすすめる
                if not self.field.parties[self.friend_player].get_fighting_poke().is_faint:
                    assert self.field.parties[self.enemy_player].get_fighting_poke().is_faint
                    enemy_fa = self._sample_enemy_action()
                    fa_list = [None, None]
                    fa_list[self.enemy_player] = enemy_fa
                    self.field.set_actions_faint_change(fa_list)
                else:
                    if self.env_rule.faint_change_random:
                        # ランダムに交代
                        fa_list = [None, None]
                        if self.field.parties[self.enemy_player].get_fighting_poke().is_faint:
                            enemy_fa = self._sample_enemy_action()
                            fa_list[self.enemy_player] = enemy_fa
                        fa_list[self.friend_player] = self._action_to_field_action(self.friend_player,
                                                                                   self.random_action_func())
                        self.field.set_actions_faint_change(fa_list)
                    else:
                        # プレイヤー側が交代の選択をしなければならないので、returnする
                        break
            if next_phase in [sim.FieldPhase.Begin, sim.FieldPhase.GameEnd]:
                break

        reward = 0.0
        if next_phase is sim.FieldPhase.Begin:
            # 前のターンでダメージを与えた量に対する報酬
            current_hp_eval = self._calc_hp_eval_score(self.friend_player)
            reward += (current_hp_eval - self.last_hp_eval_score)
            self.last_hp_eval_score = current_hp_eval
        if not action_valid:
            logger.debug("invalid action given")
            return self.make_observation(), self.reward_config.reward_invalid, True, {}
        done = False
        if next_phase is sim.FieldPhase.GameEnd:
            done = True
            winner = self.field.get_winner()
            self.result_win = self.friend_player == winner
            self.game_end = True
            reward = self.reward_config.reward_win if self.result_win else -self.reward_config.reward_win
        elif self.field.turn_number >= 63:  # 64ターン以上経過
            done = True
            self.result_draw = True
            self.game_end = True
            reward = self.reward_config.reward_draw  # 引き分けとする

        return self.make_observation(), reward, done, {}


class RandomAction:
    """
    ランダムな「合法手」を返すクラス。
    通常のenv.action_space.sampleを用いると非合法手が生じるため。
    """

    def __init__(self, env: PokeaiEnv):
        self.env = env

    def sample(self) -> int:
        vec = self.env.get_possible_action_vec(self.env.friend_player)
        return int(np.random.choice(np.flatnonzero(vec)))
