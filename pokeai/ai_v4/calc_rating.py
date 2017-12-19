"""
party_match.py の結果をもとに、各パーティの勝率・レーティングを算出する。
"""
import argparse
import pickle
import numpy as np
from . import util


def calc_win_rate_mutual(n_party, match_results):
    match_count = np.zeros((n_party,))
    win_count = np.zeros((n_party,), )
    for match_result in match_results:
        r = match_result["R"]
        left_score = r * 0.5 + 0.5  # 1,0,-1 -> 1,0.5,0
        right_score = 1.0 - left_score
        left = match_result["left"]
        right = match_result["right"]
        match_count[left] += 1
        match_count[right] += 1
        win_count[left] += left_score
        win_count[right] += right_score
    win_rate = win_count / match_count
    return win_rate


def calc_win_rate_fixed_enemies(n_party, match_results):
    match_count = np.zeros((n_party,))
    win_count = np.zeros((n_party,))
    for match_result in match_results:
        r = match_result["R"]
        left_score = r * 0.5 + 0.5  # 1,0,-1 -> 1,0.5,0
        # right_score = 1.0 - left_score
        left = match_result["left"]
        # right = match_result["right"]
        match_count[left] += 1
        # match_count[right] += 1
        win_count[left] += left_score
        # win_count[right] += right_score
    win_rate = win_count / match_count
    return win_rate


def calc_elo_rating_mutual(n_party, match_results):
    """
    ランダムな順序で戦ったとして、イロレーティングを計算する。
    :param n_party:
    :param match_results:
    :return:
    """
    ratings = np.zeros((n_party,))
    ratings[:] = 1500
    for i_mr in np.random.permutation(len(match_results)):
        match_result = match_results[i_mr]
        r = match_result["R"]
        left_score = r * 0.5 + 0.5  # 1,0,-1 -> 1,0.5,0
        right_score = 1.0 - left_score
        left = match_result["left"]
        right = match_result["right"]
        left_expected_score = 1.0 / (1.0 + 10.0 ** ((ratings[right] - ratings[left]) / 400.0))
        right_expected_score = 1.0 - left_expected_score
        ratings[left] += 32.0 * (left_score - left_expected_score)
        ratings[right] += 32.0 * (right_score - right_expected_score)
    return ratings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")

    args = parser.parse_args()
    with open(args.src, "rb") as f:
        src_data = pickle.load(f)
    entries = src_data["entries"]
    match_results = src_data["match_results"]
    enemy_parties = src_data.get("enemy_parties")

    if enemy_parties is None:
        # 相互対戦
        win_rates = calc_win_rate_mutual(len(entries), match_results)
        ratings = calc_elo_rating_mutual(len(entries), match_results)
    else:
        # ランダムパーティと対戦
        win_rates = calc_win_rate_fixed_enemies(len(entries), match_results)
        ratings = None
    with open(util.get_output_filename("rating.pickle"), "wb") as f:
        pickle.dump({"src": args.src, "win_rates": win_rates, "ratings": ratings}, f)


if __name__ == '__main__':
    main()
