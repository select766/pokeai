# -*- coding:utf-8 -*-

import numpy as np
import gym
import gym.spaces
import pokeai_simu

class PokeaiEnv():
    def __init__(self, party_generator, initial_seed, enemy_agent=None):
        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(0.0, 1.0, (16,))
        self.party_generator = party_generator
        self.seed = initial_seed
        self.enemy_agent = enemy_agent
    
    def reset(self):
        parties = self.party_generator()
        self.field = pokeai_simu.Field(parties)
        self.field.rng = pokeai_simu.BattleRngRandom(seed=self.seed)
        self.seed += 1
        self.field.logger = pokeai_simu.FieldLoggerBuffer()
        self.friend_player = 0
        return self.make_observation()
    
    def make_observation(self, from_enemy=False):
        vectors = []
        #敵から見た場合の特徴も得られる構造。敵エージェントの行動決定に用いる。
        friend_player = self.friend_player if not from_enemy else 1 - self.friend_player
        for player_id in [friend_player, 1 - friend_player]:
            party = self.field.parties[player_id]
            poke = party.get_fighting_poke()
            vectors.append(np.array([poke.hp / 1024.0, poke.static_param.max_hp / 1024.0]))

            nv_condition_vec = np.zeros((6, ))
            nv_condition_vec[poke.nv_condition.value - pokeai_simu.PokeNVCondition.Empty.value] = 1
            vectors.append(nv_condition_vec)
        return np.concatenate(vectors).astype(np.float32)
    
    def step(self, action):
        # action: int 0 to 3 which represents move index
        friend_fa = pokeai_simu.FieldActionBegin.move(action)
        if self.enemy_agent is not None:
            # 敵モデルで最善の行動をとる
            enemy_action = self.enemy_agent.act(self.make_observation(from_enemy=True))
        else:
            # ランダムプレイヤー
            enemy_action = np.random.randint(0, 4)
        enemy_fa = pokeai_simu.FieldActionBegin.move(enemy_action)

        if self.friend_player == 0:
            fa_list = [friend_fa, enemy_fa]
        else:
            fa_list = [enemy_fa, friend_fa]

        self.field.set_actions_begin(fa_list)

        while True:
            next_phase = self.field.step()
            if next_phase in [pokeai_simu.FieldPhase.Begin, pokeai_simu.FieldPhase.FaintChange, pokeai_simu.FieldPhase.GameEnd]:
                break
        
        # 交代はサポートしてない
        assert next_phase is not pokeai_simu.FieldPhase.FaintChange

        reward = 0.0
        done = False
        if next_phase is pokeai_simu.FieldPhase.GameEnd:
            done = True
            winner = self.field.get_winner()
            reward = 1.0 if self.friend_player == winner else -1.0
        elif self.field.turn_number >= 255:#256ターン以上経過
            done = True
            reward = 0.0#引き分けとする
        
        return self.make_observation(), reward, done, {}
