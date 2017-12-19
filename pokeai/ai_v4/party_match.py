"""
山登り法により生成されたパーティ同士を戦わせて勝敗・棋譜を保存する。
RLエージェントが存在する場合はそれを利用する。
"""

import os
import sys
import copy
import tempfile
from typing import List
import pickle
import argparse
from abc import ABCMeta, abstractmethod
import random
import numpy as np
from tqdm import tqdm

from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from .agents import RandomAgent
from . import pokeai_env
from . import party_generation_helper
from . import util
from . import random_rating
from . import find_train_hyper_param
from . import hill_climbing
from . import train

logger = util.get_logger(__name__)


class PartySupplier:
    """
    PokeaiEnvに外部から設定したパーティを読ませるための関数オブジェクト
    """

    def __init__(self):
        self.parties = []

    def __call__(self):
        assert len(self.parties) == 2, "parties not set to PartySupplier"
        # copy.deepcopy(self.parties) だと、自己対戦の時にシミュレータがおかしくなる(両パーティが同一インスタンスを指す状態がコピーされる？)
        return [copy.deepcopy(self.parties[0]), copy.deepcopy(self.parties[1])]


def load_rl_agent(run_id, env):
    """
    強化学習で学習したエージェントを読み込む。
    :param run_id:
    :return:
    """
    save_dir = os.path.join("run", run_id)
    run_config = util.yaml_load_file(os.path.join(save_dir, "run_config.yaml"))
    final_agent_dir = os.path.join(save_dir, "agent", f"{run_config['train']['kwargs']['steps']}_finish")
    agent = train.construct_agent(run_config, env)
    agent.load(final_agent_dir)
    return agent


def load_parties_agents(hill_climbing_path, env):
    parties, run_ids = hill_climbing.load_party_from_hill_climbing(hill_climbing_path)
    agents = []
    for run_id in run_ids:
        if run_id is not None:
            agents.append(load_rl_agent(run_id, env))
        else:
            agents.append(None)
    return parties, agents


def load_all_party_group(party_group_path, env):
    """
    すべてのパーティ・エージェントを読み込み、グループ名と対応付けた状態で返す。
    :param party_group_path:
    :return:
    """
    party_groups = util.yaml_load_file(party_group_path)
    entries = []
    for party_group in party_groups:
        hill_climbing_path = os.path.join("data", party_group["dir"], "trial_results.pickle")
        parties, agents = load_parties_agents(hill_climbing_path, env)
        for party, agent in zip(parties, agents):
            entries.append({"party": party, "agent": agent, "group": party_group["group"]})
    return entries


def match(party_left, agent_left, party_right, agent_right, env):
    env.party_generator.parties = [party_left, party_right]
    env.enemy_agent = agent_right

    obs = env.reset()
    done = False
    R = 0
    t = 0
    while not done:
        action = agent_left.act(obs)
        obs, r, done, _ = env.step(action)
        R += r
        t += 1
    agent_left.stop_episode()
    return {"R": R, "log": copy.deepcopy(env.field.logger.buffer)}


def match_mutual(entries, env, random_agent):
    match_results = []
    for i in tqdm(range(len(entries))):
        for j in range(len(entries)):
            entry_left = entries[i]
            entry_right = entries[j]
            match_result = match(entry_left["party"], entry_left["agent"] or random_agent,
                                 entry_right["party"], entry_right["agent"] or random_agent,
                                 env)
            match_result["left"] = i
            match_result["right"] = j
            match_results.append(match_result)
    return match_results


def match_fixed_enemies(entries, enemy_parties, env, random_agent):
    match_results = []
    for i in tqdm(range(len(entries))):
        for j in range(len(enemy_parties)):
            entry_left = entries[i]
            match_result = match(entry_left["party"], entry_left["agent"] or random_agent,
                                 enemy_parties[j], random_agent,
                                 env)
            match_result["left"] = i
            match_result["right"] = j
            match_results.append(match_result)
    return match_results


def save_result(path, entries, enemy_parties, match_results):
    save_obj = {}
    # agentはpickleしない
    save_obj["enemy_parties"] = enemy_parties
    save_obj["entries"] = [{"party": entry["party"], "group": entry["group"]} for entry in entries]
    save_obj["match_results"] = match_results
    with open(path, "wb") as f:
        pickle.dump(save_obj, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("party_group")
    parser.add_argument("env_rule")
    parser.add_argument("--enemy_parties",
                        help="match against specified enemy parties instead of mutually match inside party_group")

    args = parser.parse_args()
    env_rule_wrap = util.yaml_load_file(args.env_rule)
    env_config = env_rule_wrap["env"]
    env_rule = pokeai_env.EnvRule(**env_config["env_rule"])
    party_supplier = PartySupplier()
    random_agent = RandomAgent(env_rule.party_size, pokeai_env.N_MOVES, 0.1)
    env = pokeai_env.PokeaiEnv(env_rule=env_rule,
                               # 勝率に変換したいので、勝敗以外の報酬なし
                               reward_config=pokeai_env.RewardConfig(reward_win=1.0,
                                                                     reward_invalid=0.0,
                                                                     reward_damage_friend=0.0,
                                                                     reward_damage_enemy=0.0),
                               initial_seed=env_config["initial_seed"],
                               party_generator=party_supplier,
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
                               enemy_agent=random_agent)

    entries = load_all_party_group(args.party_group, env)
    if args.enemy_parties:
        with open(args.enemy_parties, "rb") as f:
            enemy_parties = pickle.load(f)
        match_results = match_fixed_enemies(entries, enemy_parties, env, random_agent)
        save_result(util.get_output_filename("match_fixed_enemies.pickle"), entries, enemy_parties, match_results)
    else:
        match_results = match_mutual(entries, env, random_agent)
        save_result(util.get_output_filename("match_mutual.pickle"), entries, None, match_results)


if __name__ == '__main__':
    main()
