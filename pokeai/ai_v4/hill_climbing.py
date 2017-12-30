"""
山登り法により、良いパーティを探索する
python -m pokeai.ai_v4.hill_climbing config_file
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
from . import pokeai_env
from . import party_generation_helper
from . import util
from . import random_rating
from . import find_train_hyper_param

logger = util.get_logger(__name__)


def generate_neighbor_parties(source_party: Party, hill_climbing_config) -> List[Party]:
    """
    近傍パーティ群の生成
    :param source_party:
    :return:
    """

    gen_parties = []  # type: List[Party]

    # ポケモンを変更したパーティの生成
    for i in range(hill_climbing_config["neighbors_poke"]):
        party = copy.deepcopy(source_party)
        # すでにパーティ中にいるポケモンと同種は除外する
        existing_dexnos = [poke.static_param.dexno for poke in party.pokes]
        while True:
            new_poke = party_generation_helper.get_random_poke()
            if new_poke.static_param.dexno in existing_dexnos:
                continue
            change_pos = random.randrange(len(party.pokes))
            party.pokes[change_pos] = new_poke
            break
        gen_parties.append(party)

    # 技を変更したパーティの生成
    for i in range(hill_climbing_config["neighbors_move"]):
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


class PartyGroupEvaluator(metaclass=ABCMeta):
    """
    パーティ群に対して評価(勝率)を計算するクラスの基底クラス
    """

    @abstractmethod
    def evaluate_parties_groups(self, parties_target: List[Party], parties_baseline: List[Party],
                                env_rule: pokeai_env.EnvRule,
                                n_play: int, show_progress=False) -> dict:
        raise NotImplementedError


class PartyGroupEvaluatorRandom:
    def __init__(self, **kwargs):
        pass

    def evaluate_parties_groups(self, parties_target: List[Party], parties_baseline: List[Party],
                                env_rule: pokeai_env.EnvRule,
                                n_play: int, show_progress=False) -> dict:
        scores = random_rating.evaluate_parties_groups(parties_target=parties_target,
                                                       parties_baseline=parties_baseline,
                                                       env_rule=env_rule,
                                                       n_play=n_play,
                                                       show_progress=show_progress)
        return {"scores": scores, "info": {}}


class PartyGroupEvaluatorRL:
    def __init__(self, base_run_config_path):
        self.base_run_config = util.yaml_load_file(base_run_config_path)

    def evaluate_parties_groups(self, parties_target: List[Party], parties_baseline: List[Party],
                                env_rule: pokeai_env.EnvRule,
                                n_play: int, show_progress=False) -> dict:
        """
        parties_targetにおいて強化学習でエージェントを学習したうえで、parties_baseline+ランダムプレイヤーに対する勝率を計算する。
        :param parties_target:
        :param parties_baseline:
        :param env_rule:
        :param n_play:
        :param show_progress:
        :return:
        """
        fd, parties_target_path = tempfile.mkstemp(".pickle")
        with os.fdopen(fd, "wb") as f:
            pickle.dump(parties_target, f)
        scores = []
        infos = []
        pbar = None
        if show_progress:
            pbar = tqdm(total=len(parties_target))
        for party_idx, party_target in enumerate(parties_target):
            run_config = copy.deepcopy(self.base_run_config)
            for phase in ["train", "eval"]:
                run_config["party_generator"][phase]["kwargs"]["friend_parties_path"] = parties_target_path
                run_config["party_generator"][phase]["kwargs"]["friend_party_idx"] = party_idx
            run_id = find_train_hyper_param.generate_unique_run_id()
            train_result = find_train_hyper_param.run_train(run_config, run_id, show_progress=False)
            final_score = train_result[run_config["train"]["kwargs"]["steps"]]["mean"]
            scores.append(final_score)
            infos.append({"train_result": train_result, "run_id": run_id})
            if show_progress:
                pbar.update()
        if show_progress:
            pbar.close()
        os.remove(parties_target_path)
        return {"scores": scores, "info": {"train_info": infos}}


party_group_evaluators = {"PartyGroupEvaluatorRandom": PartyGroupEvaluatorRandom,
                          "PartyGroupEvaluatorRL": PartyGroupEvaluatorRL}


def trial(config, evaluation_parties, initial_parties=None):
    hill_climbing_config = config["hill_climbing"]
    # 初期パーティ生成 (通常は1個だが、複数生成して最善のものを選択することも可能)
    env_rule = pokeai_env.EnvRule(**config["env"]["env_rule"])
    if initial_parties is None:
        initial_parties = [party_generation_helper.get_random_party(env_rule.party_size) for i in
                           range(hill_climbing_config.get("initial_party_size", 1))]
    party_group_evaluator = party_group_evaluators[config["party_group_evaluator"]["class"]](
        **config["party_group_evaluator"]["kwargs"])
    logger.info("Measuring initial score")
    eval_result = party_group_evaluator.evaluate_parties_groups(initial_parties, evaluation_parties, env_rule, 1,
                                                                show_progress=True)
    best_initial_party_idx = int(np.argmax(eval_result["scores"]))
    best_score = eval_result["scores"][best_initial_party_idx]
    current_party = initial_parties[best_initial_party_idx]
    logger.info(f"Initial score: {best_score}")

    trial_result = {"initial_party": current_party, "initial_score": best_score, "iterations": [],
                    "initial_eval_info": eval_result["info"], "initial_parties": initial_parties}

    for iteration in range(hill_climbing_config["iterations"]):
        logger.info(f"Iteration {iteration}")
        logger.info(f"Generating neighbor parties")
        neighbor_parties = generate_neighbor_parties(current_party, hill_climbing_config)
        logger.info(f"Evaluating neighbor parties")
        eval_result = party_group_evaluator.evaluate_parties_groups(neighbor_parties, evaluation_parties, env_rule, 1,
                                                                    show_progress=True)
        scores = eval_result["scores"]
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
                                           "best_score": best_score,
                                           "neighbor_eval_info": eval_result["info"]})
    return trial_result


def load_party_from_hill_climbing(path, get_score=False):
    """
    以前のhill climbingの実行結果における最強のパーティを読み込む。
    :param path:
    :return:
    """
    with open(path, "rb") as f:
        last_hc_result = pickle.load(f)
    parties = []
    run_ids = []
    scores = []
    for last_trial_result in last_hc_result:
        run_id = None
        if len(last_trial_result["iterations"]) > 0:
            final_iter = last_trial_result["iterations"][-1]
            scores = final_iter["neighbor_scores"]
            best_party_idx = int(np.argmax(scores))
            best_party = final_iter["neighbor_parties"][best_party_idx]
            scores.append(scores[best_party_idx])
            eval_info = final_iter["neighbor_eval_info"]
            if "train_info" in eval_info:
                run_id = eval_info["train_info"][best_party_idx]["run_id"]
        else:
            best_party = last_trial_result["initial_party"]
            scores.append(last_trial_result["initial_score"])
            eval_info = last_trial_result["initial_eval_info"]
            if "train_info" in eval_info:
                assert len(eval_info["train_info"]) == 1
                run_id = eval_info["train_info"][0]["run_id"]

        parties.append(best_party)
        run_ids.append(run_id)
    if get_score:
        return parties, run_ids, scores
    else:
        return parties, run_ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    parser.add_argument("--initial_party", help="use previous hill climbing best party as initial party")
    parser.add_argument("--trials", type=int, default=1)
    args = parser.parse_args()

    config = util.yaml_load_file(args.config)
    with open(config["evaluation_party_pool"], "rb") as f:
        evaluation_parties = pickle.load(f)

    trial_results = []
    initial_parties = None
    if args.initial_party:
        initial_parties, _ = load_party_from_hill_climbing(args.initial_party)
        assert len(initial_parties) >= args.trials
    for trial_index in range(args.trials):
        logger.info(f"Trial {trial_index}")
        trial_results.append(
            trial(config, evaluation_parties,
                  [initial_parties[trial_index]] if initial_parties is not None else None))

        # 1trialごとにファイルに書くが、書き換え中に落ちても古いファイルが残るようにする
        tmp_path = util.get_output_filename("trial_results.pickle.tmp")
        with open(tmp_path, "wb") as f:
            pickle.dump(trial_results, f)
        os.replace(tmp_path, util.get_output_filename("trial_results.pickle"))


if __name__ == '__main__':
    main()
