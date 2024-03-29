"""
山登り法でパーティ評価関数が高くなるパーティを生成する
"""

import argparse
from typing import List

import numpy as np
from bson import ObjectId
from tqdm import tqdm

from pokeai.ai.party_db import col_party
from pokeai.ai.party_feature.party_evaluator_builder import build_party_evaluator_quick_by_trainer_id
from pokeai.ai.party_feature.party_evaluator_quick import PartyEvaluatorQuick
from pokeai.ai.party_feature.party_feature_extractor import PartyFeatureExtractor
from pokeai.sim.party_generator import Party, PartyGenerator
from pokeai.sim.random_party_generator import RandomPartyGenerator

# 3vs3ならPPも含まれるほうが自然であることに注意（デフォルトはこのままで、設定側で入れる）
from pokeai.util import yaml_load

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
    parser.add_argument("config", help="設定ファイル(yaml)")
    parser.add_argument("--device", default="cuda:0", help="GPUを使う場合は'cuda:0', CPUの場合は'cpu'")
    args = parser.parse_args()
    config_file = yaml_load(args.config)
    party_generator = RandomPartyGenerator(**config_file["random_party_generator"])
    evaluator = FitnessEvaluator(
        build_party_evaluator_quick_by_trainer_id(config_file["trainer_id"], party_generator.party_size, args.device),
        party_generator._pokemons,  # 使用可能全ポケモンとの対面の平均を使う
        config_file["fitness_weight"],
    )
    seed_parties = [party_generator.generate() for _ in range(config_file["n"])]  # type: List[Party]
    dst_tags = config_file["dst_tags"]
    assert isinstance(dst_tags, list)
    generated_parties = hillclimb(evaluator=evaluator,
                                  party_generator=party_generator,
                                  seed_parties=seed_parties,
                                  generations=config_file["generations"],
                                  populations=config_file["populations"])
    parties_doc = [{'_id': ObjectId(), 'party': party, 'tags': dst_tags} for party in generated_parties]
    col_party.insert_many(parties_doc)


if __name__ == '__main__':
    main()
