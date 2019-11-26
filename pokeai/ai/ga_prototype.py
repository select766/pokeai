"""
GAによる行動学習のプロトタイプ
Deep Neuroevolutionに準拠
入力
- 対戦相手のエージェント群(tag)
- 戦略を学習するパーティのid

出力
- パラメータベクトル
- (勝率の系列)

学習対象パーティのパラメータベクトルを変化させて、ランダム戦略のパーティ群と対戦、勝率最大のものを取る
"""

import argparse
import random
from typing import List
import numpy as np
from bson import ObjectId
from tqdm import tqdm
from pokeai.ai.action_policy import ActionPolicy
from pokeai.ai.feature_extractor import FeatureExtractor
from pokeai.ai.linear_model import LinearModel
from pokeai.ai.linear_policy import LinearPolicy
from pokeai.ai.random_policy import RandomPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.sim import Sim
from pokeai.util import pickle_load, pickle_dump
from pokeai.sim.party_generator import Party
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from pokeai.ai.rating_battle import load_agent


def add_noise(model: LinearModel, std: float):
    """
    モデルにノイズを加えて次の候補とする
    :param model:
    :param std:
    :return:
    """
    model.intercept_ += np.random.normal(scale=std, size=model.intercept_.shape)
    model.coef_ += np.random.normal(scale=std, size=model.coef_.shape)


def generate_next_generations(model: LinearModel, size: int, std: float):
    models = []
    for _ in range(size):
        newmodel = model.copy()
        add_noise(newmodel, std)
        models.append(newmodel)
    return models


def fitness(sim, feature_extractor, fitness_policies, fitness_parties, target_party, target_model):
    bsp_t = BattleStreamProcessor()
    bsp_t.set_policy(LinearPolicy(feature_extractor, target_model))
    wins = 0
    for fitness_policy, fitness_party in zip(fitness_policies, fitness_parties):
        bsp_f = BattleStreamProcessor()
        bsp_f.set_policy(fitness_policy)
        sim.set_processor([bsp_t, bsp_f])
        sim.set_party([target_party, fitness_party])
        result = sim.run()  # {'winner': 'p1',...}
        if result['winner'] == 'p1':
            wins += 1
    return wins / len(fitness_parties)


def ga(fitness_policies, fitness_parties, target_party, generations, populations, selections, std):
    sim = Sim()
    feature_extractor = FeatureExtractor()
    initial_model = LinearModel(feature_dims=feature_extractor.get_dims(), action_dims=18)
    current_models = [initial_model] * selections
    current_fitnesses = [0.0] * selections
    for gen in tqdm(range(generations)):
        cand_models = []
        cand_fitnesses = []
        for pop in range(populations):
            base_model = random.choice(current_models)
            cand_model = base_model.copy()
            add_noise(base_model, std=std)
            cand_fitness = fitness(sim, feature_extractor, fitness_policies, fitness_parties, target_party, cand_model)
            cand_models.append(cand_model)
            cand_fitnesses.append(cand_fitness)
        # TODO: elite
        order = np.argsort(cand_fitnesses)[::-1]
        print(f"gen {gen} fitnesses {np.sort(cand_fitnesses)}")
        next_fitnesses = []
        next_models = []
        for idx in order[:selections]:
            next_models.append(cand_models[idx])
            next_fitnesses.append(cand_fitnesses[idx])
        current_fitnesses = next_fitnesses
        current_models = next_models
    return LinearPolicy(feature_extractor, current_models[0])


def main():
    import logging
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("party_id", help="学習対象のパーティID")
    parser.add_argument("agent_tags", help="エージェントのタグ(カンマ区切り)")
    parser.add_argument("dst_agent_tags")
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--populations", type=int, default=100)
    parser.add_argument("--selections", type=int, default=10)
    parser.add_argument("--std", type=float, default=0.1)
    args = parser.parse_args()
    fitness_parties = []
    fitness_policies = []
    # agent_tagsのいずれかのタグを含むエージェントを列挙
    for agent_doc in col_agent.find({"tags": {"$in": args.agent_tags.split(",")}}):
        party, policy = load_agent(agent_doc)
        fitness_parties.append(party)
        fitness_policies.append(policy)
    target_party_doc = col_party.find_one({'_id': ObjectId(args.party_id)})
    target_party = target_party_doc['party']
    trained_policy = ga(fitness_policies, fitness_parties, target_party,
                        args.generations, args.populations, args.selections, args.std)
    trained_agent_id = ObjectId()
    col_agent.insert_one({
        '_id': trained_agent_id,
        'party_id': target_party_doc['_id'],
        'policy_packed': pack_obj(trained_policy),
        'tags': args.dst_agent_tags.split(',')
    })
    print(f"trained agent id: {trained_agent_id}")


if __name__ == '__main__':
    main()
