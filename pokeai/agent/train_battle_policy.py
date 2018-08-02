"""
バトルの方策を強化学習で学習する
"""

import os
import argparse
from typing import Dict, List, Tuple
import copy
import pickle
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import logging
import sys
import gym

from pokeai.agent.party_generator import PartyGenerator, PartyRule
from pokeai.agent.poke_env import PokeEnv
from pokeai.sim import Field
from pokeai.sim.dexno import Dexno
from pokeai.sim.field import FieldPhase
from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.game_rng import GameRNGRandom
from pokeai.sim.move import Move
from pokeai.sim.party import Party
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.poke_type import PokeType
from pokeai.sim import context
from pokeai.agent.util import load_pickle, save_pickle

gym.undo_logger_setup()  # Turn off gym's default logger settings
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='')


def train(outdir: str, friend_party: Party, enemy_pool: List[Party]):
    env = PokeEnv(friend_party, enemy_pool, feature_types="enemy_type hp_ratio nv_condition".split(" "))
    obs_size = env.observation_space.shape[0]
    n_actions = env.action_space.n
    q_func = chainerrl.q_functions.FCStateQFunctionWithDiscreteAction(
        obs_size, n_actions,
        n_hidden_layers=2, n_hidden_channels=50)

    optimizer = chainer.optimizers.Adam(eps=1e-2)
    optimizer.setup(q_func)

    # Set the discount factor that discounts future rewards.
    gamma = 0.95

    # Use epsilon-greedy for exploration
    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.3, random_action_func=env.action_space.sample)

    # DQN uses Experience Replay.
    # Specify a replay buffer and its capacity.
    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10 ** 6)

    # Now create an agent that will interact with the environment.
    agent = chainerrl.agents.DoubleDQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, update_interval=1,
        target_update_interval=100)

    chainerrl.experiments.train_agent_with_evaluation(
        agent, env,
        steps=100000,  # Train the agent for 100000 steps
        eval_n_runs=100,  # 10 episodes are sampled for each evaluation
        max_episode_len=200,  # Maximum length of each episodes
        eval_interval=10000,  # Evaluate the agent after every 10000 steps
        outdir=outdir)  # Save everything to 'result' directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("friend_pool")
    parser.add_argument("enemy_pool")
    parser.add_argument("--count", type=int, default=-1, help="いくつのパーティについて方策を学習するか")
    parser.add_argument("--skip", type=int, default=0)
    args = parser.parse_args()
    context.init()
    friend_pool = load_pickle(args.friend_pool)["parties"]  # type: List[Party]
    enemy_pool = load_pickle(args.enemy_pool)["parties"]  # type: List[Party]
    os.makedirs(args.dst)
    count = args.count
    if count < 0:
        count = len(friend_pool) - args.skip
    for i in range(args.skip, args.skip + count):
        outdir = os.path.join(args.dst, f"party_{i}")
        train(outdir, friend_pool[i], enemy_pool)


if __name__ == '__main__':
    main()
