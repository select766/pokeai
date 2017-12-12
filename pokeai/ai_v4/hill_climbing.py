"""
山登り法により、良いパーティを探索する
python -m pokeai.ai_v4.hill_climbing party_file
"""

import copy
from typing import List
import pickle
import argparse
import random
import numpy as np
from tqdm import tqdm

from pokeai.sim import MoveID, Dexno, PokeType, PokeStaticParam, Poke, Party
from . import pokeai_env
from . import party_generation_helper
from . import util
from . import random_rating

logger = util.get_logger(__name__)


def generate_neighbor_parties(source_party: Party, args) -> List[Party]:
    """
    近傍パーティ群の生成
    :param source_party:
    :return:
    """

    gen_parties = []  # type: List[Party]

    # ポケモンを変更したパーティの生成
    for i in range(args.neighbors_poke):
        party = copy.deepcopy(source_party)
        party.pokes[random.randrange(len(party.pokes))] = party_generation_helper.get_random_poke()
        gen_parties.append(party)

    # 技を変更したパーティの生成
    for i in range(args.neighbors_move):
        party = copy.deepcopy(source_party)
        poke = party.pokes[random.randrange(len(party.pokes))]
        poke_move_ids = poke.static_param.move_ids
        # 同じ技を2つ覚えることはできないので、それに注意して技をランダムに変更
        while True:
            new_move = random.choice(party_generation_helper.available_moves)
            if new_move not in poke_move_ids:
                poke_move_ids[random.randrange(len(poke_move_ids))] = new_move
                break
        gen_parties.append(party)

    return gen_parties


def trial(args, evaluation_parties):
    # 初期パーティ生成
    current_party = party_generation_helper.get_random_party(args.party_size)
    env_rule = pokeai_env.EnvRule(args.party_size, faint_change_random=True)
    logger.info("Measuring initial score")
    initial_score_array = random_rating.evaluate_parties_groups([current_party], evaluation_parties, env_rule, 1,
                                                                show_progress=True)

    best_score = initial_score_array[0]
    logger.info(f"Initial score: {best_score}")

    trial_result = {"initial_party": current_party, "initial_score": best_score, "iterations": []}

    for iteration in range(args.iterations):
        logger.info(f"Iteration {iteration}")
        logger.info(f"Generating neighbor parties")
        neighbor_parties = generate_neighbor_parties(current_party, args)
        logger.info(f"Evaluating neighbor parties")
        scores = random_rating.evaluate_parties_groups(neighbor_parties, evaluation_parties, env_rule, 1,
                                                       show_progress=True)
        best_party_idx = int(np.argmax(scores))
        best_party_score = scores[best_party_idx]
        if best_party_score > best_score:
            logger.info(f"Best score updated to {best_party_score}")
            best_score = best_party_score
            current_party = neighbor_parties[best_party_idx]
        else:
            logger.info("Best score not updated")
        trial_result["iterations"].append({"best_party": current_party,
                                           "neighbor_parties": neighbor_parties,
                                           "neighbor_scores": scores,
                                           "best_score": best_score})
    return trial_result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evaluation_party_pool")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--neighbors_move", type=int, default=10)
    parser.add_argument("--neighbors_poke", type=int, default=3)
    parser.add_argument("--party_size", type=int, default=3)
    args = parser.parse_args()

    with open(args.evaluation_party_pool, "rb") as f:
        evaluation_parties = pickle.load(f)

    trial_results = []
    for trial_index in range(args.trials):
        logger.info(f"Trial {trial_index}")
        trial_results.append(trial(args, evaluation_parties))

    with open(util.get_output_filename("trial_results.pickle"), "wb") as f:
        pickle.dump(trial_results, f)


if __name__ == '__main__':
    main()
