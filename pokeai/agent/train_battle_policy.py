"""
バトルの方策を強化学習で学習する
"""

import os
import argparse
from typing import Dict, List, Tuple
import chainerrl
import logging
import sys
from bson import ObjectId
from pokeai.agent import party_db
from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_agents import load_agent
from pokeai.agent.battle_observer import BattleObserver
from pokeai.agent.poke_env import PokeEnv, RewardConfig
from pokeai.sim.party_template import PartyTemplate
from pokeai.sim import context
from pokeai.agent.util import load_pickle, save_pickle, load_yaml
import pokeai.agent.agent_builder

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
# suppress message from chainerrl (output on every episode)
train_agent_logger = logging.getLogger("chainerrl.experiments.train_agent")
train_agent_logger.setLevel(logging.WARNING)


def train(outdir: str, agent_id: ObjectId, friend_party_t: PartyTemplate, agent_params,
          enemy_agents: List[BattleAgent]):
    party_size = len(friend_party_t.poke_sts)
    observer_kwargs = {"party_size": party_size}
    observer_kwargs.update(agent_params["observer"])
    observer = BattleObserver(**observer_kwargs)
    reward_config = RewardConfig(**agent_params["reward"])

    env = PokeEnv(friend_party_t, observer, enemy_agents, reward_config)

    agent = pokeai.agent.agent_builder.build(agent_params, observer)

    train_config = agent_params["train"]
    steps = train_config["steps"]
    train_kwargs = {
        "max_episode_len": 100,
        "eval_n_runs": 100,
        "eval_interval": 10000,
    }
    train_kwargs.update(train_config)
    chainerrl.experiments.train_agent_with_evaluation(
        agent, env,
        outdir=outdir,
        **train_kwargs)

    model_dump_dir = os.path.join(outdir, f"{steps}_finish")  # 最終的なモデルの出力ディレクトリ
    return {
        "_id": agent_id,
        "party_id": friend_party_t.party_id,
        "class_name": "BattleAgentRl",
        "agent": {"params": agent_params, "model_dump_dir": model_dump_dir},
        "observer": observer_kwargs
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dst")
    parser.add_argument("agent_tag")
    parser.add_argument("friend_party_group_tag")
    parser.add_argument("enemy_agent_tag")
    parser.add_argument("agent_params")
    args = parser.parse_args()
    context.init()
    agent_params = load_yaml(args.agent_params)
    party_group = party_db.load_party_group(args.friend_party_group_tag)

    enemy_agents = []
    for agent_info in party_db.col_agent.find({"tags": args.enemy_agent_tag}):
        enemy_agents.append(load_agent(agent_info))
    print(f"enemy agents: {len(enemy_agents)}")
    os.makedirs(args.dst)
    for friend_party_t in party_group:
        agent_id = ObjectId()
        outdir = os.path.join(args.dst, str(agent_id))
        os.makedirs(outdir)
        agent_info = train(outdir, agent_id, friend_party_t, agent_params, enemy_agents)
        agent_info["tags"] = [args.agent_tag]
        party_db.col_agent.insert_one(agent_info)


if __name__ == '__main__':
    main()
