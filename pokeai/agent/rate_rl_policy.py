"""
強化学習エージェントのレーティング戦を行う。
強化学習したパーティ、そのパーティをランダムな行動で動かすもの、ランダムな行動で動かすパーティを参加させる。
"""
import os
import random
import argparse
from typing import Dict, List, Tuple, Callable, Optional
import copy
import pickle
import glob

import chainer
import chainerrl
import numpy as np
from tqdm import tqdm

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
from pokeai.agent.common import match_random_policy
from pokeai.agent.util import load_pickle, save_pickle


def rating_battle(env: PokeEnv, parties: List[Party], action_samplers: List[Optional[Callable[[np.ndarray], int]]],
                  match_count: int) -> Tuple[List[float], list]:
    """
    パーティ同士を多数戦わせ、レーティングを算出する。
    :param parties:
    :param match_count:
    :return: パーティのレーティング
    """
    assert len(parties) % 2 == 0
    rates = np.full((len(parties),), 1500.0)
    logs = []
    for i in range(match_count):
        # 対戦相手を決める
        # レーティングに乱数を加算し、ソートして隣接パーティ同士を戦わせる
        rates_with_random = rates + np.random.normal(scale=200., size=rates.shape)
        ranking = np.argsort(rates_with_random)
        for j in range(0, len(parties), 2):
            left = ranking[j]
            right = ranking[j + 1]
            log = []
            winner = env.match_agents([parties[left], parties[right]], [action_samplers[left], action_samplers[right]],
                                      lambda obj: log.append(obj))
            logs.append({"party_idxs": [left, right], "winner": winner, "log": log})
            # レートを変動させる
            if winner >= 0:
                left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0))
                if winner == 0:
                    left_incr = 32 * (1.0 - left_winrate)
                else:
                    left_incr = 32 * (-left_winrate)
                rates[left] += left_incr
                rates[right] -= left_incr
        abs_mean_diff = np.mean(np.abs(rates - 1500.0))
        print(f"{i} rate mean diff: {abs_mean_diff}")
    return rates.tolist(), logs


def load_agent(env: PokeEnv, agent_dir):
    obs_size = env.observation_space.shape[0]
    n_actions = env.action_space.n
    q_func = chainerrl.q_functions.FCStateQFunctionWithDiscreteAction(
        obs_size, n_actions,
        n_hidden_layers=2, n_hidden_channels=32)

    optimizer = chainer.optimizers.Adam(eps=1e-2)
    optimizer.setup(q_func)

    # Set the discount factor that discounts future rewards.
    gamma = 0.95

    # Use epsilon-greedy for exploration
    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.1, random_action_func=env.action_space.sample)

    # DQN uses Experience Replay.
    # Specify a replay buffer and its capacity.
    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10 ** 6)

    # Now create an agent that will interact with the environment.
    agent = chainerrl.agents.DoubleDQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, update_interval=1,
        target_update_interval=100)

    agent.load(agent_dir)

    return agent.act


def load_parties_agents(env: PokeEnv, party_file_path: str):
    """
    パーティおよびそのエージェントをロードする。
    :param party_file_path:
    :return:
    """
    parties_with_meta = load_pickle(party_file_path)["parties"]
    parties = []
    action_samplers = []
    metadata = []
    for party_with_meta in parties_with_meta:
        party = party_with_meta["party"]
        party_uuid = party_with_meta["uuid"]
        agent_dirs = glob.glob(os.path.join(os.path.dirname(party_file_path), party_uuid, "*_finish"))
        if len(agent_dirs) > 0:
            action_sampler = load_agent(env, agent_dirs[0])
            parties.append(party)
            action_samplers.append(action_sampler)
            metadata.append({"uuid": party_uuid, "policy": "rl"})

        # 同じパーティで、ランダム行動エージェント版も追加
        parties.append(party)
        action_samplers.append(None)
        metadata.append({"uuid": party_uuid, "policy": "random"})
    return parties, action_samplers, metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("party_file", nargs="+")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    args = parser.parse_args()
    context.init()
    dummy_party = load_pickle(args.party_file[0])["parties"][0]["party"]
    env = PokeEnv(dummy_party, [dummy_party],
                  feature_types="enemy_type hp_ratio nv_condition rank fighting_idx alive_idx".split(" "))
    parties = []
    action_samplers = []
    metadata = []
    print("loading parties")
    for pf in args.party_file:
        p, a, m = load_parties_agents(env, pf)
        parties.extend(p)
        action_samplers.extend(a)
        metadata.extend(m)
    print("rating")
    rates, log = rating_battle(env, parties, action_samplers, args.match_count)
    save_pickle({"parties": parties, "party_metadatas": metadata, "rates": rates, "log": log}, args.dst)


if __name__ == '__main__':
    main()
