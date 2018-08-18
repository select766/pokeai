"""
train_battle_policyで学習したモデルのレーティング測定。
ランダム方策、定数方策(どれか1つの技だけ出し続ける)と比較する。
"""

import os
import argparse
from typing import Dict, List, Tuple, Callable
import copy
import pickle
import logging
import sys
import glob
import random
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
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
from pokeai.agent.util import load_pickle, save_pickle, save_yaml, load_party_rate


def match_policy(env: PokeEnv, enemy_party: Party, action_sampler: Callable[[np.ndarray], int]) -> int:
    obs = env.reset(enemy_party)
    done = False
    reward = 0
    while not done:
        action = action_sampler(obs)
        obs, reward, done, _ = env.step(action)
    if reward == 0:
        winner = -1
    elif reward > 0:
        winner = 0
    else:
        winner = 1
    return winner


def rating_single_party(env: PokeEnv, parties: List[Party], party_rates: np.ndarray, match_count: int,
                        action_sampler: Callable[[np.ndarray], int],
                        initial_rate: float = 1500.0,
                        reject_rate: float = 0.0) -> float:
    """
    あるパーティを、レーティングが判明している別パーティ群と戦わせてレーティングを計算する。
    :return: パーティのレーティング
    """
    rate = initial_rate
    for i in range(match_count):
        # 対戦相手を決める
        rate_with_random = rate + np.random.normal(scale=200.)
        nearest_party_idx = int(np.argmin(np.abs(party_rates - rate_with_random)))
        winner = match_policy(env, parties[nearest_party_idx], action_sampler)
        # レートを変動させる
        if winner >= 0:
            left_winrate = 1.0 / (1.0 + 10.0 ** ((party_rates[nearest_party_idx] - rate) / 400.0))
            if winner == 0:
                left_incr = 32 * (1.0 - left_winrate)
            else:
                left_incr = 32 * (-left_winrate)
            rate += left_incr
            if rate < reject_rate:
                # 明らかに弱く、山登り法で採用の可能性がない場合に打ち切る
                break
    return float(rate)


def eval_agent(agent_dir: str, friend_party: Party, enemy_pool: List[Party], enemy_pool_rates: List[float]):
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

    agent.load(agent_dir)

    rates = {}
    rates["agent"] = rating_single_party(env, enemy_pool, np.array(enemy_pool_rates), len(enemy_pool), agent.act)

    # ランダム戦略
    rates["random"] = rating_single_party(env, enemy_pool, np.array(enemy_pool_rates), len(enemy_pool),
                                          lambda x: random.randrange(4))

    # 定数戦略
    for move_idx in range(4):
        rates[f"const_{move_idx}"] = rating_single_party(env, enemy_pool, np.array(enemy_pool_rates), len(enemy_pool),
                                                         lambda x: move_idx)
    return rates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("agents_pool")
    parser.add_argument("friend_pool")
    parser.add_argument("test_enemy_pool")
    parser.add_argument("test_enemy_pool_rate")
    parser.add_argument("--count", type=int, default=-1, help="いくつのパーティについて方策を学習するか")
    parser.add_argument("--skip", type=int, default=0)
    args = parser.parse_args()
    context.init()
    friend_pool = [p["party"] for p in load_pickle(args.friend_pool)["parties"]]  # type: List[Party]
    test_enemy_pool, test_enemy_pool_rates = load_party_rate(args.test_enemy_pool, args.test_enemy_pool_rate)
    count = args.count
    if count < 0:
        count = len(friend_pool) - args.skip
    for i in range(args.skip, args.skip + count):
        party_dir = os.path.join(args.agents_pool, f"party_{i}")
        outdir = glob.glob(os.path.join(party_dir, "*_finish"))[0]
        friend_party = friend_pool[i]
        rates = eval_agent(outdir, friend_party, test_enemy_pool, test_enemy_pool_rates)
        print(friend_party)
        print(rates)
        result = {"rates": rates, "party_str": str(friend_party)}
        save_yaml(result, os.path.join(party_dir, "eval.yaml"))


if __name__ == '__main__':
    main()
