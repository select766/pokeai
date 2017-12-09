#!/usr/bin/env python
# -*- coding:utf-8 -*-
# run as "python -m ai_v4.train [options]"

import sys
import os
import logging
from logging import getLogger
import argparse
import time
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import gym
import gym.spaces
from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from . import util
from . import pokeai_env

logging.basicConfig(level=logging.INFO)
logger = getLogger(__name__)


def generate_run_id():
    """
    学習試行にIDを与え、またデータを保存するディレクトリを作成する。
    :return: (run_id, save_dir)
    """
    run_id = time.strftime("%Y%m%d%H%M%S")
    project_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    save_dir = os.path.join(project_root_dir, "run", run_id)
    os.makedirs(save_dir)
    return run_id, save_dir


def construct_model(model_config, obs_size, n_actions):
    assert model_config["class"] == "FCStateQFunctionWithDiscreteAction"
    from chainerrl.q_functions import FCStateQFunctionWithDiscreteAction
    model_class = FCStateQFunctionWithDiscreteAction
    model_instance = model_class(ndim_obs=obs_size, n_actions=n_actions,
                                 **model_config["kwargs"])
    return model_instance


def construct_agent(run_config, env: pokeai_env.PokeaiEnv):
    model = construct_model(run_config["model"], env.observation_space.shape[0], env.action_space.n)

    optimizer_config = run_config["train"]["optimizer"]
    assert optimizer_config["class"] == "Adam"
    from chainer.optimizers import Adam
    optimizer = Adam(**optimizer_config["kwargs"])
    optimizer.setup(model)

    agent_config = run_config["agent"]
    explorer_config = agent_config["explorer"]
    assert explorer_config["class"] == "ConstantEpsilonGreedy"
    from chainerrl.explorers import ConstantEpsilonGreedy
    random_action = pokeai_env.RandomAction(env)
    explorer = ConstantEpsilonGreedy(**explorer_config["kwargs"],
                                     random_action_func=random_action.sample)
    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=agent_config["replay_buffer_capacity"])

    assert agent_config["class"] == "DQN"
    from chainerrl.agents import DQN
    agent = DQN(q_function=model,
                optimizer=optimizer,
                replay_buffer=replay_buffer,
                explorer=explorer,
                **agent_config["kwargs"])

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


def load_party_generator(path):
    import importlib.machinery
    module = importlib.machinery.SourceFileLoader("party_generator", path).load_module()
    return getattr(module, "generate_parties")


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_config")
    parser.add_argument("party_generator")
    parser.add_argument("--eval", help="specify directory of model.npz")

    args = parser.parse_args()

    run_config = util.yaml_load_file(args.run_config)
    generate_parties_func = load_party_generator(args.party_generator)

    if not args.eval:
        run_id, save_dir = generate_run_id()

    env_config = run_config["env"]
    env = pokeai_env.PokeaiEnv(env_rule=pokeai_env.EnvRule(**env_config["env_rule"]),
                               reward_config=pokeai_env.RewardConfig(**env_config["reward_config"]),
                               initial_seed=env_config["initial_seed"],
                               party_generator=generate_parties_func,
                               observers=[pokeai_env.ObserverPossibleAction(),
                                          pokeai_env.ObserverFightingPoke(from_enemy=False,
                                                                          nv_condition=True,
                                                                          v_condition=False,
                                                                          rank=False),
                                          pokeai_env.ObserverFightingPoke(from_enemy=True,
                                                                          nv_condition=True,
                                                                          v_condition=False,
                                                                          rank=False)
                                          ],
                               enemy_agent=None)

    agent = construct_agent(run_config, env)

    if args.eval:
        agent.load(args.eval)
        train_kwargs = run_config["train"]["kwargs"]
        for i in range(train_kwargs["eval_n_runs"]):
            obs = env.reset()
            done = False
            R = 0
            t = 0
            while not done and t < 200:
                # env.render()
                action = agent.act(obs)
                obs, r, done, _ = env.step(action)
                R += r
                t += 1
            print('test episode:', i, 'R:', R)
            for log_line in env.field.logger.buffer:
                print(log_line)
            agent.stop_episode()

    else:
        chainerrl.experiments.train_agent_with_evaluation(
            agent,
            env,
            outdir=os.path.join(save_dir, "agent"),
            **run_config["train"]["kwargs"]
        )


if __name__ == '__main__':
    train()
