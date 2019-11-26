"""
山登り法でパーティ評価関数が高くなるパーティを生成する
"""

import argparse
import pickle
import os
from typing import List, Tuple

import numpy as np
from bson import ObjectId

from pokeai.ai.party_db import col_party, col_agent, col_rate
from pokeai.ai.party_feature.party_rate_predictor import PartyRatePredictor
from pokeai.sim.party_generator import Party, PartyGenerator
from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.util import pickle_dump, yaml_load, yaml_dump, pickle_load


def hillclimb(predictor: PartyRatePredictor, party_generator: PartyGenerator, seed_parties: List[Party],
              generations: int, populations: int):
    current_parties = seed_parties
    for gen in range(generations):
        next_parties = []
        next_rates = []
        for current_party in current_parties:
            candidates = [party_generator.neighbor(current_party) for _ in range(populations - 1)] + [current_party]
            candidate_rates = predictor.predict(candidates)
            best_rated_idx = int(np.argmax(candidate_rates))
            next_parties.append(candidates[best_rated_idx])
            next_rates.append(candidate_rates[best_rated_idx])
        print(f"gen {gen} mean rates: {np.mean(next_rates)}")
        current_parties = next_parties
    return current_parties


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("predictor", help="学習済評価関数")
    parser.add_argument("seed_tags", help="変更元にするパーティのタグ")
    parser.add_argument("dst_tags", help="生成パーティの保存タグ")
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--populations", type=int, default=10)
    args = parser.parse_args()
    predictor = pickle_load(args.predictor)  # type: PartyRatePredictor
    seed_parties = []  # type: List[Party]
    for party_doc in col_party.find({"tags": {"$in": args.seed_tags.split(",")}}):
        seed_parties.append(party_doc["party"])
    dst_tags = args.dst_tags.split(",")
    party_generator = RandomPartyGenerator()
    generated_parties = hillclimb(predictor=predictor,
                                  party_generator=party_generator,
                                  seed_parties=seed_parties,
                                  generations=args.generations,
                                  populations=args.populations)
    parties_doc = [{'_id': ObjectId(), 'party': party, 'tags': dst_tags} for party in generated_parties]
    col_party.insert_many(parties_doc)


if __name__ == '__main__':
    main()
