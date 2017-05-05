# -*- coding:utf-8 -*-

import numpy as np
import gym
import gym.spaces
import pokeai_simu

N_POKEMON_SPECIES=9
N_MOVES=20
FIGHTING_POKE_STATUS_DIMS=N_POKEMON_SPECIES+N_MOVES+20
BENCH_POKE_STATUS_DIMS=N_POKEMON_SPECIES+N_MOVES+9

class PokeaiEnv():
    def __init__(self, party_size, party_generator, initial_seed, enemy_agent=None, reward_damage=False, faint_change_random=False):
        self.action_space = gym.spaces.Discrete(N_MOVES + party_size * 2)#技、交代先、ひんし交代先
        self.party_size = party_size
        # 状態ベクトル 「選べる行動ベクトル」「出ているポケモンを示すバイナリベクトル」「出ているポケモンのステータスベクトル」「控えのポケモンのステータスベクトル」 行動以外は自分と相手で２倍
        self.obs_vector_size = (N_MOVES + party_size * 2) + (party_size + FIGHTING_POKE_STATUS_DIMS + BENCH_POKE_STATUS_DIMS * party_size) * 2
        self.observation_space = gym.spaces.Box(0.0, 1.0, (self.obs_vector_size,))
        self.party_generator = party_generator
        self.seed = initial_seed
        self.enemy_agent = enemy_agent
        self.reward_damage = reward_damage
        self.faint_change_random = faint_change_random
    
    def reset(self):
        parties = self.party_generator()
        self.field = pokeai_simu.Field(parties)
        self.field.rng = pokeai_simu.BattleRngRandom(seed=self.seed)
        self.seed += 1
        self.field.logger = pokeai_simu.FieldLoggerBuffer()
        self.friend_player = 0
        self.enemy_player = 1 - self.friend_player
        self.last_hp_eval_score = self._calc_hp_eval_score(self.friend_player)
        return self.make_observation()
    
    def get_possible_action_vec(self, player):
        party_size = self.party_size
        vec = np.zeros((N_MOVES + party_size * 2), dtype=np.float32)
        party = self.field.parties[player]
        living_bench_pokes = [int(not poke.is_faint) for poke in party.pokes]
        living_bench_pokes[party.fighting_poke_idx] = 0

        if self.field.phase is pokeai_simu.FieldPhase.Begin:
            #技・交代選択
            f_poke = party.get_fighting_poke()
            if f_poke.move_handler is not None:
                #連続技発動中なので、それしか選べない
                move_id = f_poke.move_handler.move_entry.move_id
                vec[move_id.value - 1] = 1
            else:
                #すべての技+生きている控え
                for move_id in f_poke.static_param.move_ids:
                    vec[move_id.value - 1] = 1
                vec[N_MOVES:N_MOVES+party_size] = living_bench_pokes
        elif self.field.phase is pokeai_simu.FieldPhase.FaintChange:
            #ひんしによる交代選択
            vec[N_MOVES+party_size:] = living_bench_pokes
        return vec
    
    def get_fighting_poke_vec(self, poke):
        vec = np.zeros((FIGHTING_POKE_STATUS_DIMS, ), dtype=np.float32)
        vec[poke.static_param.dexno.value - 1] = 1
        for move_id in poke.static_param.move_ids:
            vec[N_POKEMON_SPECIES + move_id.value - 1] = 1
        ofs = N_POKEMON_SPECIES + N_MOVES
        vec[ofs+0] = int(not poke.is_faint)
        vec[ofs+1] = poke.hp / 1024.0
        vec[ofs+2] = poke.static_param.max_hp / 1024.0
        #状態異常６種類
        vec[ofs+3 + poke.nv_condition.value - pokeai_simu.PokeNVCondition.Empty.value] = 1
        vec[ofs+9] = int(poke.confusion_turn > 0)
        vec[ofs+10] = int(poke.bad_poison)
        vec[ofs+11] = min(poke.bad_poison_turn / 16.0, 1.0)
        vec[ofs+12] = int(poke.reflect)
        vec[ofs+13] = int(poke.digging)
        vec[ofs+14] = poke.rank_a / 12.0 + 0.5
        vec[ofs+15] = poke.rank_b / 12.0 + 0.5
        vec[ofs+16] = poke.rank_c / 12.0 + 0.5
        vec[ofs+17] = poke.rank_s / 12.0 + 0.5
        vec[ofs+18] = poke.rank_accuracy / 12.0 + 0.5
        vec[ofs+19] = poke.rank_evasion / 12.0 + 0.5
        return vec

    def get_bench_poke_vec(self, poke):
        vec = np.zeros((BENCH_POKE_STATUS_DIMS, ), dtype=np.float32)
        vec[poke.static_param.dexno.value - 1] = 1
        for move_id in poke.static_param.move_ids:
            vec[N_POKEMON_SPECIES + move_id.value - 1] = 1
        ofs = N_POKEMON_SPECIES + N_MOVES
        vec[ofs+0] = int(not poke.is_faint)
        vec[ofs+1] = poke.hp / 1024.0
        vec[ofs+2] = poke.static_param.max_hp / 1024.0
        #状態異常６種類
        vec[ofs+3 + poke.nv_condition.value - pokeai_simu.PokeNVCondition.Empty.value] = 1
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
        hp_diff = self._calc_total_hp(self.field.parties[friend_player]) - self._calc_total_hp(self.field.parties[1 - friend_player])
        hp_score = hp_diff / 1024.0
        return hp_score
    
    def make_observation(self, from_enemy=False):
        vectors = []
        #敵から見た場合の特徴も得られる構造。敵エージェントの行動決定に用いる。
        friend_player = self.friend_player if not from_enemy else self.enemy_player
        vectors.append(self.get_possible_action_vec(friend_player))
        for player in [friend_player, 1 - friend_player]:
            party = self.field.parties[player]
            fighting_poke_idx_vec = np.zeros((self.party_size, ), dtype=np.float32)
            fighting_poke_idx_vec[party.fighting_poke_idx] = 1
            vectors.append(fighting_poke_idx_vec)
            vectors.append(self.get_fighting_poke_vec(party.get_fighting_poke()))

            #for poke in party.pokes:
            #    vectors.append(self.get_bench_poke_vec(poke))
        return np.concatenate(vectors).astype(np.float32)
    
    def correct_action(self, player, action):
        """
        現在可能な行動かどうかを判定し、不正な行動であればランダムに可能な行動に置き換える
        (actionが可能な行動かどうか, 補正された行動)を返す。
        actionがNoneの場合、可能な範囲のランダムな行動を返す。
        """
        possible_action_vec = self.get_possible_action_vec(player)
        if action is not None and possible_action_vec[action] != 0:
            #OK
            return True, action
        else:
            #だめなのでランダム選択
            return False, np.random.choice(np.flatnonzero(possible_action_vec))

    def random_action_func(self):
        _, action = self.correct_action(self.friend_player, None)
        return action
    
    def _action_to_field_action(self, player, action):
        if action < N_MOVES:
            move_idx = self.field._get_fighting_poke(player).static_param.move_ids.index(pokeai_simu.MoveID(action + 1))
            assert move_idx >= 0
            return pokeai_simu.FieldActionBegin.move(move_idx)
        elif action < N_MOVES + self.party_size:
            return pokeai_simu.FieldActionBegin.change(action - N_MOVES)
        else:
            return pokeai_simu.FieldActionFaintChange(action - (N_MOVES + self.party_size))

    def _sample_enemy_action(self):
        if self.enemy_agent is not None:
            # 敵モデルで最善の行動をとる
            enemy_action = self.enemy_agent.act(self.make_observation(from_enemy=True))
        else:
            # ランダムプレイヤー
            enemy_action = None
            # TODO: 今は交代を選ばないようにしているが、学習がうまくいくようになれば解除
            possible_action_vec = self.get_possible_action_vec(self.enemy_player)
            possible_action_vec[N_MOVES:N_MOVES+self.party_size] = 0#交代を選ばない
            enemy_action = np.random.choice(np.flatnonzero(possible_action_vec))
        #敵モデルが不正な行動を取る可能性もあるので訂正しておく
        _, enemy_corrected_action = self.correct_action(self.enemy_player, enemy_action)
        enemy_fa = self._action_to_field_action(self.enemy_player, enemy_corrected_action)
        return enemy_fa
    
    def step(self, action):
        # action: int 0 to 3 which represents move index
        enemy_action_needed = False
        if self.field.phase is pokeai_simu.FieldPhase.Begin:
            # 技または交代
            action_valid, corrected_action = self.correct_action(self.friend_player, action)
            friend_fa = self._action_to_field_action(self.friend_player, corrected_action)
            enemy_action_needed = True

        elif self.field.phase is pokeai_simu.FieldPhase.FaintChange:
            #ひんし交代
            #プレイヤーがひんしになっているときのみ
            action_valid, corrected_action = self.correct_action(self.friend_player, action)
            friend_fa = self._action_to_field_action(self.friend_player, corrected_action)
            if self.field.parties[self.enemy_player].get_fighting_poke().is_faint:
                #敵側もひんしなので、交代の行動選択
                enemy_action_needed = True

        if enemy_action_needed:
            enemy_fa = self._sample_enemy_action()
        else:
            enemy_fa = None


        if self.friend_player == 0:
            fa_list = [friend_fa, enemy_fa]
        else:
            fa_list = [enemy_fa, friend_fa]

        if self.field.phase is pokeai_simu.FieldPhase.Begin:
            self.field.set_actions_begin(fa_list)
        elif self.field.phase is pokeai_simu.FieldPhase.FaintChange:
            self.field.set_actions_faint_change(fa_list)

        while True:
            next_phase = self.field.step()
            if next_phase is pokeai_simu.FieldPhase.FaintChange:
                #敵側のみが交代であれば、自動で選択してすすめる
                if not self.field.parties[self.friend_player].get_fighting_poke().is_faint:
                    assert self.field.parties[self.enemy_player].get_fighting_poke().is_faint
                    enemy_fa = self._sample_enemy_action()
                    fa_list = [None, None]
                    fa_list[self.enemy_player] = enemy_fa
                    self.field.set_actions_faint_change(fa_list)
                else:
                    if self.faint_change_random:
                        # ランダムに交代
                        fa_list = [None, None]
                        if self.field.parties[self.enemy_player].get_fighting_poke().is_faint:
                            enemy_fa = self._sample_enemy_action()
                            fa_list[self.enemy_player] = enemy_fa
                        fa_list[self.friend_player] = self._action_to_field_action(self.friend_player, self.random_action_func())
                        self.field.set_actions_faint_change(fa_list)
                    else:
                        #プレイヤー側が交代の選択をしなければならないので、returnする
                        break
            if next_phase in [pokeai_simu.FieldPhase.Begin, pokeai_simu.FieldPhase.GameEnd]:
                break
        
        reward = -0.01
        if next_phase is pokeai_simu.FieldPhase.Begin:
            if self.reward_damage:
                #前のターンでダメージを与えた量に対する報酬
                current_hp_eval = self._calc_hp_eval_score(self.friend_player)
                reward += current_hp_eval - self.last_hp_eval_score
                self.last_hp_eval_score = current_hp_eval
        if not action_valid:
            reward += -0.1#間接的にまずい行動であることを学習させる
            return self.make_observation(), -10.0, True, {}
        done = False
        if next_phase is pokeai_simu.FieldPhase.GameEnd:
            done = True
            winner = self.field.get_winner()
            reward = 1.0 if self.friend_player == winner else -1.0
        elif self.field.turn_number >= 63:#64ターン以上経過
            done = True
            reward = 0.0#引き分けとする
        
        return self.make_observation(), reward, done, {}
