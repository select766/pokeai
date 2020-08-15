"""
山登り法でパーティ評価関数が高くなるパーティを生成する
"""

import argparse
from typing import List, Tuple

import numpy as np
from bson import ObjectId
from tqdm import tqdm

from pokeai.ai.party_db import col_party
from pokeai.ai.party_feature.party_evaluator_quick import PartyEvaluatorQuick, build_party_evaluator_quick_by_trainer_id
from pokeai.ai.party_feature.party_feature_extractor import PartyFeatureExtractor
from pokeai.sim.party_generator import Party, PartyGenerator
from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.util import pickle_dump, yaml_load, yaml_dump, pickle_load

WEIGHT_PARAMS_DEFAULT = {
    "party_feature_names": ["P", "M", "PM", "MM"],
    "party_feature_penalty": 0.01,
}


class FitnessEvaluator:
    def __init__(self, party_evaluator: PartyEvaluatorQuick, opponent_pokes: List[str], weight_params: dict):
        self.party_evaluator = party_evaluator
        self.opponent_pokes = opponent_pokes
        self.weight_params = WEIGHT_PARAMS_DEFAULT.copy()
        self.weight_params.update(weight_params)
        self.party_feature_extractor = PartyFeatureExtractor(self.weight_params["party_feature_names"])
        self.existing_parties_feature = None

    def set_existing_parties(self, parties: List[Party]):
        """
        類似度ペナルティ計算用の既存パーティを設定する
        :param parties:
        :return:
        """
        self.existing_parties_feature = np.mean(np.vstack(
            [self.party_feature_extractor.get_feature(party) for party in parties]), axis=0)

    def evaluate(self, party: Party) -> float:
        q_value = np.mean(self.party_evaluator.gather_best_q(party, self.opponent_pokes))
        penalty = 0.0
        if self.existing_parties_feature is not None:
            feat = self.party_feature_extractor.get_feature(party)
            penalty = (feat @ self.existing_parties_feature) * self.weight_params[
                "party_feature_penalty"]
        return float(q_value - penalty)


def hillclimb(evaluator: FitnessEvaluator, party_generator: PartyGenerator, seed_parties: List[Party],
              generations: int, populations: int):
    generated_parties = []
    for seed_party in tqdm(seed_parties):
        current_party = seed_party
        for gen in range(generations):
            candidates = [party_generator.neighbor(current_party) for _ in range(populations - 1)] + [current_party]
            candidate_rates = [evaluator.evaluate(candidate) for candidate in candidates]
            best_rated_idx = int(np.argmax(candidate_rates))
            current_party = candidates[best_rated_idx]
        generated_parties.append(current_party)
        evaluator.set_existing_parties(generated_parties)
    return generated_parties


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trainer_id", help="評価関数として用いるQ関数")
    parser.add_argument("dst_tags", help="生成パーティの保存タグ")
    parser.add_argument("-r", default="default", help="regulation")
    parser.add_argument("-n", type=int, default=100, help="生成パーティ数")
    parser.add_argument("--generations", type=int, default=10, help="世代数")
    parser.add_argument("--populations", type=int, default=100, help="1世代あたりの候補パーティ数")
    parser.add_argument("--party_feature_penalty", type=float, default=WEIGHT_PARAMS_DEFAULT["party_feature_penalty"])
    args = parser.parse_args()
    party_generator = RandomPartyGenerator(regulation=args.r, neighbor_poke_change_rate=0.1,
                                           neighbor_item_change_rate=0.0)
    evaluator = FitnessEvaluator(
        build_party_evaluator_quick_by_trainer_id(ObjectId(args.trainer_id)),
        party_generator._learnsets.keys(),  # 使用可能全ポケモンとの対面の平均を使う
        {"party_feature_penalty": args.party_feature_penalty},
    )
    seed_parties = [party_generator.generate() for _ in range(args.n)]  # type: List[Party]
    dst_tags = args.dst_tags.split(",")
    generated_parties = hillclimb(evaluator=evaluator,
                                  party_generator=party_generator,
                                  seed_parties=seed_parties,
                                  generations=args.generations,
                                  populations=args.populations)
    parties_doc = [{'_id': ObjectId(), 'party': party, 'tags': dst_tags} for party in generated_parties]
    col_party.insert_many(parties_doc)


if __name__ == '__main__':
    main()
