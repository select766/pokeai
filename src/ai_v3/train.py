#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
from logging import getLogger
logger = getLogger(__name__)
import argparse
import json
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import gym
import gym.spaces
import util
import pokeai_simu
import pokeai_env
import party_generator

PARTY_SIZE = 3


def my_party():
    pokes = []

    MoveID = pokeai_simu.MoveID
    Dexno = pokeai_simu.Dexno
    PokeType = pokeai_simu.PokeType
    PokeStaticParam = pokeai_simu.PokeStaticParam
    Poke = pokeai_simu.Poke

    poke = PokeStaticParam()
    poke.dexno = Dexno.Starmie
    poke.move_ids = [MoveID.Splash, MoveID.Thunderbolt,
                     MoveID.Toxic, MoveID.BodySlam]
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Psychc
    poke.max_hp = 167
    poke.st_a = 127
    poke.st_b = 137
    poke.st_c = 152
    poke.st_s = 167
    poke.base_s = 115
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Lapras
    poke.move_ids = [MoveID.Reflect, MoveID.Thunderbolt,
                     MoveID.Psychic, MoveID.NightShade]
    poke.type1 = PokeType.Water
    poke.type2 = PokeType.Ice
    poke.max_hp = 237
    poke.st_a = 137
    poke.st_b = 132
    poke.st_c = 147
    poke.st_s = 112
    poke.base_s = 60
    pokes.append(Poke(poke))

    poke = PokeStaticParam()
    poke.dexno = Dexno.Dugtrio
    poke.move_ids = [MoveID.Toxic, MoveID.DoubleTeam,
                     MoveID.Slash, MoveID.NightShade]
    poke.type1 = PokeType.Ground
    poke.type2 = PokeType.Empty
    poke.max_hp = 142
    poke.st_a = 132
    poke.st_b = 102
    poke.st_c = 122
    poke.st_s = 172
    poke.base_s = 120
    pokes.append(Poke(poke))

    assert len(pokes) == PARTY_SIZE
    return pokeai_simu.Party(pokes)


def generate_parties():
    return [my_party(), party_generator.get_random_party(PARTY_SIZE)]


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


def show_party(party, print_func):
    for i, poke in enumerate(party.pokes):
        st = poke.static_param
        s = ""
        if i == party.fighting_poke_idx:
            s += "*"
        else:
            s += " "
        s += st.dexno.name + " "
        for move_id in st.move_ids:
            s += move_id.name + " "
        s += "HP {}/{} ".format(poke.hp, st.max_hp)
        print_func(s)


def show_parties(parties, print_func):
    for player in [0, 1]:
        print_func("Player {}".format(player))
        show_party(parties[player], print_func)


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.py")
    parser.add_argument("--model_class", default="QFunction")
    parser.add_argument("--model_args", default='{"n_obs":130, "n_action":26, "n_hidden":128}')  # json
    parser.add_argument("--suffix")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--enemy_agent")
    parser.add_argument("--reward_damage", action="store_true")
    parser.add_argument("--alpha", type=float, default=0.001)

    args = parser.parse_args()
    util.init(args.suffix)

    if args.enemy_agent is not None:
        enemy_agent = load_agent(args.enemy_agent)
    else:
        enemy_agent = None

    import copy
    static_party = generate_parties()
    env = pokeai_env.PokeaiEnv(PARTY_SIZE, generate_parties, 1, enemy_agent,
                               reward_damage=args.reward_damage, faint_change_random=True)
    model_args_obj = json.loads(args.model_args.replace('\'', '"'))
    q_func = construct_model(args.model, args.model_class, model_args_obj)

    optimizer = chainer.optimizers.Adam(alpha=args.alpha)
    optimizer.setup(q_func)
    gamma = 0.95

    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.1, random_action_func=env.random_action_func
    )

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10 ** 6)

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
            logger.info(f'episode: {i}, R: {R}, statistics: {agent.get_statistics()}')
        agent.stop_episode_and_train(obs, reward, done)
    logger.info('Finished.')

    agent.save(util.get_output_dir())
    save_agent_meta(util.get_output_dir(), args.model, args.model_class, model_args_obj)

    test_sum_R = 0.0
    n_test = 100
    for i in range(n_test):
        obs = env.reset()
        show_parties(env.field.parties, logger.debug)
        done = False
        R = 0
        t = 0
        while not done and t < 200:
            # env.render()
            action = agent.act(obs)
            obs, r, done, _ = env.step(action)
            R += r
            t += 1
        logger.info(f'test episode:{i} R: {R}')
        test_sum_R += R
        logger.debug("Episode log begin")
        for log_entry in env.field.logger.buffer:
            logger.debug(str(log_entry))
        logger.debug("Episode log end")
        agent.stop_episode()
    logger.info("Average R: {}".format(test_sum_R / n_test))


if __name__ == '__main__':
    train()
