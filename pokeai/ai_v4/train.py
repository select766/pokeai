#!/usr/bin/env python
# -*- coding:utf-8 -*-
# run as "python -m pokeai.ai_v4.train [options]"

import sys
import os
from logging import getLogger
import argparse
import time
import numpy as np
import chainer
import chainerrl
import gym
import gym.spaces
from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from . import util
from . import pokeai_env
from .agents import RandomAgent

logger = util.get_logger(__name__)


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


def load_party_generator(path, run_config, phase_eval):
    import importlib.machinery
    module = importlib.machinery.SourceFileLoader("party_generator", path).load_module()
    if hasattr(module, "generate_parties"):
        # function形式
        return getattr(module, "generate_parties")
    elif hasattr(module, "PartyGenerator"):
        # class形式
        return getattr(module, "PartyGenerator")(
            **run_config["party_generator"]["eval" if phase_eval else "train"]["kwargs"])


def train():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_config")
    parser.add_argument("party_generator")
    parser.add_argument("--eval", help="specify directory of model.npz")

    args = parser.parse_args()

    run_config = util.yaml_load_file(args.run_config)
    generate_parties_func_train = load_party_generator(args.party_generator, run_config, phase_eval=False)
    generate_parties_func_eval = load_party_generator(args.party_generator, run_config, phase_eval=True)

    save_dir = None
    if not args.eval:
        save_dir = util.get_output_dir()
        util.yaml_dump_file(run_config, os.path.join(save_dir, "run_config.yaml"))

    env_config = run_config["env"]
    env_rule = pokeai_env.EnvRule(**env_config["env_rule"])
    env = pokeai_env.PokeaiEnv(env_rule=env_rule,
                               reward_config=pokeai_env.RewardConfig(**env_config["reward_config"]),
                               initial_seed=env_config["initial_seed"],
                               party_generator=generate_parties_func_train,
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
                               enemy_agent=RandomAgent(env_rule.party_size, pokeai_env.N_MOVES, 0.1))
    eval_env = pokeai_env.PokeaiEnv(env_rule=env_rule,
                                    # 勝率に変換したいので、勝敗以外の報酬なし
                                    reward_config=pokeai_env.RewardConfig(reward_win=1.0,
                                                                          reward_invalid=0.0,
                                                                          reward_damage_friend=0.0,
                                                                          reward_damage_enemy=0.0),
                                    initial_seed=env_config["initial_seed"],
                                    party_generator=generate_parties_func_eval,
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
                                    enemy_agent=RandomAgent(env_rule.party_size, pokeai_env.N_MOVES, 0.1))

    agent = construct_agent(run_config, env)

    if args.eval:
        agent.load(args.eval)
        train_kwargs = run_config["train"]["kwargs"]
        for i in range(train_kwargs["eval_n_runs"]):
            obs = env.reset()
            done = False
            R = 0
            t = 0
            while not done:
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
            eval_env=eval_env,
            **run_config["train"]["kwargs"]
        )


if __name__ == '__main__':
    train()
