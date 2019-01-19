"""
山登り法+強化学習でパーティ生成
現在パーティを少し変化させて生成したパーティの戦略を強化学習で学習させ、強いパーティを次世代に残す。
"""
import os
import argparse
import shutil
from multiprocessing.pool import Pool
from typing import Dict, List, Tuple, Callable, Optional
import copy
import pickle
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import logging
import sys
import uuid
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
from pokeai.agent.util import load_pickle, save_pickle, reset_random, load_party_rate

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
# suppress message from chainerrl (output on every episode)
train_agent_logger = logging.getLogger("chainerrl.experiments.train_agent")
train_agent_logger.setLevel(logging.WARNING)


class PartyTrainEvaluator:
    """
    パーティの戦略を学習し、強さを測定する機構
    """
    enemy_pool: List[Party]
    enemy_pool_rate: np.ndarray
    match_count: int
    feature_types: List[str]

    def __init__(self, enemy_pool: List[Party], enemy_pool_rate: np.ndarray, match_count: int):
        self.enemy_pool = enemy_pool
        self.enemy_pool_rate = enemy_pool_rate
        self.match_count = match_count
        self.feature_types = "enemy_type hp_ratio nv_condition rank fighting_idx alive_idx".split(" ")

    def train_and_evaluate(self, friend_party: Party, baseline_rate: float, outdir: str) -> float:
        """
        パーティの戦略を学習し、強さを測定する
        :param friend_party:
        :return: 強さ(レーティング)
        """
        env = PokeEnv(friend_party, self.enemy_pool, feature_types=self.feature_types)
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

        chainerrl.experiments.train_agent_with_evaluation(
            agent, env,
            steps=100000,  # Train the agent for 100000 steps
            eval_n_runs=100,  # 10 episodes are sampled for each evaluation
            max_episode_len=200,  # Maximum length of each episodes
            eval_interval=10000,  # Evaluate the agent after every 10000 steps
            outdir=outdir)  # Save everything to 'result' directory

        rate = self.rating_single_party(env, self.enemy_pool, self.enemy_pool_rate, self.match_count, agent.act,
                                        baseline_rate, baseline_rate - 400.0)
        return rate

    def match_policy(self, env: PokeEnv, enemy_party: Party, action_sampler: Callable[[np.ndarray], int]) -> int:
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

    def rating_single_party(self, env: PokeEnv, parties: List[Party], party_rates: np.ndarray, match_count: int,
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
            # 対戦相手にもランダムに値を加算する。さもないと、rateが十分高い場合に最上位の相手としか当たらなくなる。
            party_rates_with_random = party_rates + np.random.normal(scale=200., size=party_rates.shape)
            nearest_party_idx = int(np.argmin(np.abs(party_rates_with_random - rate_with_random)))
            winner = self.match_policy(env, parties[nearest_party_idx], action_sampler)
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


def hill_climbing_mp(args):
    return hill_climbing(*args)


def hill_climbing(partygen: PartyGenerator, seed_party: Party, baseline_parties, baseline_rates, neighbor: int,
                  iter: int,
                  match_count: int,
                  dst_dir: str):
    party_uuid = str(uuid.uuid4())
    party = seed_party
    party_rate = 1500.0
    pte = PartyTrainEvaluator(baseline_parties, baseline_rates, match_count)
    uuids = set()
    uuids.add(party_uuid)
    party_rate = pte.train_and_evaluate(party, party_rate, os.path.join(dst_dir, party_uuid))
    history = []
    history.append((party, party_rate, party_uuid))
    for i in range(iter):
        neighbors = []
        neighbor_rates = []
        neighbor_uuids = []
        for n in range(neighbor):
            new_party = partygen.generate_neighbor_party(party)
            new_party_uuid = str(uuid.uuid4())
            uuids.add(new_party_uuid)
            new_rate = pte.train_and_evaluate(new_party, party_rate, os.path.join(dst_dir, new_party_uuid))
            neighbors.append(new_party)
            neighbor_rates.append(new_rate)
            neighbor_uuids.append(new_party_uuid)
        print(f"{party_uuid} {i} rates: {neighbor_rates}")
        best_neighbor_idx = int(np.argmax(neighbor_rates))
        if neighbor_rates[best_neighbor_idx] > party_rate:
            print(f"rate up: {party_rate} => {neighbor_rates[best_neighbor_idx]}")
            party_rate = neighbor_rates[best_neighbor_idx]
            party = neighbors[best_neighbor_idx]
            party_uuid = neighbor_uuids[best_neighbor_idx]
        history.append((party, party_rate, party_uuid))
        print(party)
    print(f"rate: {party_rate}")
    # 全部の強化学習結果を残すと巨大なので削除する
    for unused_uuid in uuids:
        if unused_uuid == party_uuid:
            continue
        unused_uuid_dir = os.path.join(dst_dir, unused_uuid)
        if os.path.exists(unused_uuid_dir):
            shutil.rmtree(unused_uuid_dir)
    return party, party_rate, party_uuid, history


def process_init():
    reset_random()
    context.init()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst_dir")
    parser.add_argument("seed_party")
    parser.add_argument("baseline_party_pool", help="レーティング測定相手パーティ群")
    parser.add_argument("baseline_party_rate", help="レーティング測定相手パーティ群のレーティング")
    # parser.add_argument("n_party", type=int)
    parser.add_argument("--rule", choices=[r.name for r in PartyRule], default=PartyRule.LV55_1.name)
    parser.add_argument("--neighbor", type=int, default=10, help="生成する近傍パーティ数")
    parser.add_argument("--iter", type=int, default=100, help="iteration数")
    parser.add_argument("--match_count", type=int, default=100, help="1パーティあたりの対戦回数")
    parser.add_argument("-j", type=int, help="並列処理数")
    args = parser.parse_args()
    context.init()
    baseline_parties, baseline_rates = load_party_rate(args.baseline_party_pool, args.baseline_party_rate)
    partygen = PartyGenerator(PartyRule[args.rule])
    results = []
    os.makedirs(args.dst_dir)
    seed_parties = [p["party"] for p in load_pickle(args.seed_party)["parties"]]
    with Pool(processes=args.j, initializer=process_init) as pool:
        args_list = []
        for seed_party in seed_parties:
            args_list.append((partygen, seed_party, baseline_parties, baseline_rates, args.neighbor, args.iter,
                              args.match_count, args.dst_dir))
        for generated_party, rate, party_uuid, history_result in pool.imap_unordered(hill_climbing_mp, args_list):
            # 1サンプル生成ごとに呼ばれる(全計算が終わるまで待たない)
            results.append(
                {"party": generated_party, "uuid": party_uuid, "optimize_rate": rate, "history": history_result})
            print(f"completed {len(results)} / {len(seed_parties)}")
    save_pickle({"parties": results}, os.path.join(args.dst_dir, "parties.bin"))


if __name__ == '__main__':
    main()
