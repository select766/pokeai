# -*- coding:utf-8 -*-

import sys
import os
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import numpy as np
import gym
import gym.spaces
import pokeai_simu
import pokeai_env

def party_generator():
    return [party_generator_one(), party_generator_one()]

def party_generator_one():
    pokes = []

    poke = pokeai_simu.PokeStaticParam()
    poke.dexno = pokeai_simu.Dexno.Alakazam
    MoveID = pokeai_simu.MoveID
    poke.move_ids = [MoveID.Thunderbolt, MoveID.Toxic,
                     MoveID.Recover, MoveID.Splash]
    poke.type1 = pokeai_simu.PokeType.Psychc
    poke.type2 = pokeai_simu.PokeType.Empty
    poke.max_hp = 162
    poke.st_a = 102
    poke.st_b = 97
    poke.st_c = 187
    poke.st_s = 172
    poke.base_s = 120
    pokes.append(pokeai_simu.Poke(poke))

    return pokeai_simu.Party(pokes)

class QFunction(chainer.Chain):
    def __init__(self):
        super().__init__(
            fc1=L.Linear(16, 10),
            fc2=L.Linear(10, 4)
        )
    
    def __call__(self, x, test=False):
        h = x
        h = F.relu(self.fc1(h))
        h = self.fc2(h)
        return chainerrl.action_value.DiscreteActionValue(h)

def train():
    env = pokeai_env.PokeaiEnv(party_generator, 1)
    q_func = QFunction()

    optimizer = chainer.optimizers.Adam()
    optimizer.setup(q_func)
    gamma = 0.95

    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.1, random_action_func=env.action_space.sample
    )

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10**6)

    agent = chainerrl.agents.DoubleDQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, update_frequency=1,
        target_update_frequency=100
    )

    n_episodes = 10000
    for i in range(n_episodes):
        obs = env.reset()
        reward = 0
        done = False
        R = 0
        t = 0
        while not done:
            action = agent.act_and_train(obs, reward)
            obs, reward, done, _ = env.step(action)
            R += reward
            t += 1
        if i % 10 == 0:
            print('episode:', i,
                  'R:', R,
                  'statistics:', agent.get_statistics())
        agent.stop_episode_and_train(obs, reward, done)
    print('Finished.')

    for i in range(10):
        obs = env.reset()
        done = False
        R = 0
        t = 0
        while not done and t < 200:
            #env.render()
            action = agent.act(obs)
            obs, r, done, _ = env.step(action)
            R += r
            t += 1
        print('test episode:', i, 'R:', R)
        for log_entry in env.field.logger.buffer:
            print(str(log_entry))
        agent.stop_episode()

if __name__ == '__main__':
    train()
