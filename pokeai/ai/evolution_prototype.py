"""
進化計算による行動学習のプロトタイプ
入力
- パーティ群
- 戦略を学習するパーティのindex

出力
- パラメータベクトル
- (勝率の系列)

学習対象パーティのパラメータベクトルを変化させて、ランダム戦略のパーティ群と対戦、勝率最大のものを取る
"""

import argparse
from typing import List
import numpy as np
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


def random_battle(sim: Sim, agent_party, random_parties):
    wins = 0
    for i in range(len(random_parties)):
        sim.set_party([agent_party, random_parties[i]])
        result = sim.run()  # {'winner': 'p1',...}
        if result['winner'] == 'p1':
            wins += 1
    return wins / len(random_parties)


def battles(sim: Sim, model: LinearModel,
            size: int,
            std: float,
            feature_extractor: FeatureExtractor,
            agent_party: Party,
            random_parties: List[Party]):
    gen_models = generate_next_generations(model, size, std)
    win_rates = []
    for i, gen_model in tqdm(enumerate(gen_models)):
        bsp_agent = BattleStreamProcessor()
        bsp_agent.set_policy(LinearPolicy(feature_extractor, gen_model))
        bsp_random = BattleStreamProcessor()
        bsp_random.set_policy(RandomPolicy())
        sim.set_processor([bsp_agent, bsp_random])
        win_rate = random_battle(sim, agent_party, random_parties)
        win_rates.append(win_rate)
    print("win_rates", win_rates)
    best_idx = int(np.argmax(win_rates))
    return gen_models[best_idx], win_rates[best_idx]


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("parties")
    parser.add_argument("dst")
    parser.add_argument("--agent_idx", type=int, default=0)
    parser.add_argument("--gen", type=int, default=10)
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--std", type=float, default=0.1)
    args = parser.parse_args()
    parties = pickle_load(args.parties)  # type: List[Party]
    sim = Sim()
    feature_extractor = FeatureExtractor()
    model = LinearModel(feature_dims=feature_extractor.get_dims(), action_dims=18)
    win_rate = None
    for gen in range(args.gen):
        new_model, win_rate = battles(sim=sim,
                                      model=model,
                                      size=args.size,
                                      std=args.std,
                                      feature_extractor=feature_extractor,
                                      agent_party=parties[args.agent_idx],
                                      random_parties=parties)
        print(f"win rate: {win_rate}")
        model = new_model
    pickle_dump({"model": model, "win_rate": win_rate}, args.dst)


if __name__ == '__main__':
    main()
