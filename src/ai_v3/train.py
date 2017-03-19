#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import argparse
import json
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import gym
import gym.spaces
import pokeai_simu
import pokeai_env
import party_generator

PARTY_SIZE=3

def generate_parties():
    return [party_generator.get_random_party(PARTY_SIZE), party_generator.get_random_party(PARTY_SIZE)]

def construct_model(model_def_path, class_name, kwargs):
    from importlib import machinery
    loader = machinery.SourceFileLoader('model', model_def_path)
    module = loader.load_module()
    model_class = getattr(module, class_name)
    model_instance = model_class(**kwargs)
    return model_instance

def save_agent_meta(save_dir, model_def_path, class_name, kwargs):
    import shutil
    shutil.copy(model_def_path, os.path.join(save_dir, "model.py"))
    with open(os.path.join(save_dir, "model.json"), "w") as f:
        json.dump({"class_name": class_name, "kwargs": kwargs}, f)

def load_agent(save_dir):
    with open(os.path.join(save_dir, "model.json")) as f:
        metadata = json.load(f)
    
    q_func = construct_model(os.path.join(save_dir, "model.py"), metadata["class_name"], metadata["kwargs"])

    # unnecessary objects for testing
    optimizer = chainer.optimizers.Adam()
    optimizer.setup(q_func)
    gamma = 0.95

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10)

    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.1, random_action_func=None
    )

    optimizer = chainer.optimizers.Adam()
    optimizer.setup(q_func)
    agent = chainerrl.agents.DQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, update_frequency=1,
        target_update_frequency=100
    )

    agent.load(save_dir)

    return agent

def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.py")
    parser.add_argument("--model_class", default="QFunction")
    parser.add_argument("--model_args", default='{"n_obs":358, "n_action":26, "n_hidden":128}')#json
    parser.add_argument("--save_dir", default="trained_agent")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--enemy_agent")
    parser.add_argument("--reward_damage", action="store_true")
    parser.add_argument("--alpha", type=float, default=0.001)

    args = parser.parse_args()

    if args.enemy_agent is not None:
        enemy_agent = load_agent(args.enemy_agent)
    else:
        enemy_agent = None

    env = pokeai_env.PokeaiEnv(PARTY_SIZE, generate_parties, 1, enemy_agent, reward_damage=args.reward_damage)
    model_args_obj = json.loads(args.model_args.replace('\'', '"'))
    q_func = construct_model(args.model, args.model_class, model_args_obj)

    optimizer = chainer.optimizers.Adam(alpha=args.alpha)
    optimizer.setup(q_func)
    gamma = 0.95

    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.1, random_action_func=env.random_action_func
    )

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10**6)

    agent = chainerrl.agents.DQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, update_frequency=1,
        target_update_frequency=100
    )

    for i in range(args.episodes):
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

    agent.save(args.save_dir)
    save_agent_meta(args.save_dir, args.model, args.model_class, model_args_obj)

    test_sum_R = 0.0
    n_test = 10
    for i in range(n_test):
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
        test_sum_R += R
        for log_entry in env.field.logger.buffer:
            print(str(log_entry))
        agent.stop_episode()
    print("Average R: {}".format(test_sum_R / n_test))

if __name__ == '__main__':
    train()
