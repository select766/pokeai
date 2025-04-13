"""
Double Oracleに基づいてパーティを生成していくベースライン
"""
import argparse
from collections.abc import Callable
import json
import time

import numpy as np
import torch
import nashpy
from pokeai.ai.selection.party_match_dataset_feat import get_party_feat
from pokeai.ai.selection.party_match_model import PartyMatchModel
from pokeai.sim.party_generator import Party, PartyGenerator
from pokeai.sim.random_party_generator import RandomPartyGenerator
from pokeai.util import json_load, pickle_dump

def get_selected_parties(party: Party) -> list[Party]:
    """
    パーティの選出の全組み合わせを取得する関数
    """
    selected_parties = []
    # ここでは、ポケモンを1匹選出する組み合わせを取得
    # 例えば、[1, 2, 3] -> [[1], [2], [3]]のようにする
    for poke in party:
        selected_parties.append([poke])
    return selected_parties

def get_party_payoff_by_nash(parties: list[Party], selected_party_payoff_fn: Callable[[Party, Party], float]) -> float:
    """
    2つのパーティを対戦させた際の利得を計算する関数
    選出にはナッシュ均衡に基づく混合戦略を用いる
    """
    assert len(parties) == 2, "parties must be 2"
    # 選出後のポケモンの組み合わせを取得
    row_payoff = np.zeros((len(parties[0]), len(parties[1])))
    sp0 = get_selected_parties(parties[0])
    sp1 = get_selected_parties(parties[1])
    for i, sub_party_0 in enumerate(sp0):
        for j, sub_party_1 in enumerate(sp1):
            # ここでは、ポケモンの組み合わせを対戦させる
            # 例えば、[1] vs [2]のようにする
            row_payoff[i][j] = selected_party_payoff_fn(sub_party_0, sub_party_1)
    # ナッシュ均衡を計算
    game = nashpy.Game(row_payoff)
    # 混合戦略を計算
    mixed_strategy = game.linear_program()
    nash_payoff = game[mixed_strategy]
    return nash_payoff[0]  # パーティ1の利得を返す

def find_mixed_strategy_of_parties(parties: list[Party], selected_party_payoff_fn: Callable[[Party, Party], float]) -> np.ndarray:
    """
    パーティ集合の混合戦略を計算する関数
    パーティの集合があるとき、どのパーティをどの確率で選択するかを計算する
    """

    # パーティ間の利得表を計算
    n = len(parties)
    parties_payoff = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            parties_payoff[i][j] = get_party_payoff_by_nash([parties[i], parties[j]], selected_party_payoff_fn)
            parties_payoff[j][i] = -parties_payoff[i][j]

    # ナッシュ均衡を計算
    game = nashpy.Game(parties_payoff)
    mixed_strategy = game.linear_program()
    # 混合戦略を返す
    return mixed_strategy[0]  # 対称なので、どちらでも良い

def generate_best_party(party_set: list[Party], party_set_mixed_strategy: np.ndarray, selected_party_payoff_fn: Callable[[Party, Party], float], gen: PartyGenerator,
                        hill_climb_iterations: int, neighbor_iterations: int) -> Party:
    """
    現在のパーティ集合に対して利得が最大となるパーティを生成する関数
    """

    def get_payoff_ageinst_party_set(party: Party) -> float:
        """
        選択確率付きパーティ集合に対して、パーティの利得を計算する関数
        """
        # まずは、パーティ集合の混合戦略を計算
        payoff = 0.0
        for i, existing_party in enumerate(party_set):
            if party_set_mixed_strategy[i] > 0:
                payoff += party_set_mixed_strategy[i] * get_party_payoff_by_nash([party, existing_party], selected_party_payoff_fn)
        return payoff

    # 混合戦略に基づいて、パーティを生成
    best_party = gen.generate()
    best_payoff = get_payoff_ageinst_party_set(best_party)
    # 山登り法を使う
    for i in range(hill_climb_iterations):
        # ランダムに作成した近傍パーティで一番良いものを選択
        for j in range(neighbor_iterations):
            neighbor = gen.neighbor(best_party)
            # 近傍パーティの利得を計算
            payoff = get_payoff_ageinst_party_set(neighbor)
            if payoff > best_payoff:
                best_party = neighbor
                best_payoff = payoff
    return {"party": best_party, "payoff": best_payoff}

class PartyEvaluator:
    def __init__(self, feat_map_path: str, model_path: str):
        self.model = PartyMatchModel()
        self.model.load_state_dict(torch.load(model_path, weights_only=True))
        self.model.eval()
        self.mapping = json_load(feat_map_path)["mapping"]
    
    def __call__(self, party1: Party, party2: Party) -> float:
        """
        2つのパーティを対戦させた際の利得を計算する関数
        :param party1:
        :param party2:
        :return: 利得
        """
        # 特徴量を取得
        feat1 = get_party_feat(party1, self.mapping)
        feat2 = get_party_feat(party2, self.mapping)
        # モデルに入力して利得を計算
        with torch.no_grad():
            payoff = self.model(torch.tensor([feat1]), torch.tensor([feat2]))
            return payoff.item()

def main():
    """
    DOのサイクル
    パーティ集合の混合戦略を計算
    パーティ候補を生成して、パーティ集合と対戦させて利得を計算
    利得が最大かつ0以上のパーティをパーティ集合に追加

    対戦では、パーティの選出組み合わせ(3*3)ごとに利得をシミュレーション（何度もやって平均）し、ナッシュ均衡ベースで選出して利得を決定

    パーティ候補は山登り法で改良していく
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="output path (pickle)")
    parser.add_argument("-r", default="default", help="regulation")
    parser.add_argument("--feat_map", required=True, help="mapping path (json)")
    parser.add_argument("--model", required=True, help="model path (pytorch)")
    parser.add_argument("--hill_climb_iterations", type=int, default=10, help="number of hill climbing iterations")
    parser.add_argument("--neighbor_iterations", type=int, default=10, help="number of neighbor iterations")
    parser.add_argument("--num_cycles", type=int, default=100, help="number of cycles")
    args = parser.parse_args()
    gen = RandomPartyGenerator(regulation=args.r)

    model = PartyEvaluator(args.feat_map, args.model)

    party_set = [gen.generate()]
    party_set_mixed_strategy = np.ones(len(party_set)) / len(party_set)
    time_start = time.time()

    for cycle in range(args.num_cycles):
        # パーティ候補を生成して、パーティ集合と対戦させて利得を計算
        best_party = generate_best_party(party_set, party_set_mixed_strategy, model, gen, hill_climb_iterations=args.hill_climb_iterations, neighbor_iterations=args.neighbor_iterations)
        elapsed = time.time() - time_start
        print("Cycle:", cycle, "Elapsed time:", elapsed, "seconds")
        print("generated party", best_party["party"], "payoff", best_party["payoff"])
        # 利得が最大かつ0以上のパーティをパーティ集合に追加
        if best_party["payoff"] > 0:
            party_set.append(best_party["party"])
            # パーティ集合の混合戦略を計算
            party_set_mixed_strategy = find_mixed_strategy_of_parties(party_set, model)
        pickle_dump({"cycle": cycle, "party_set": party_set, "mixed_strategy": party_set_mixed_strategy}, args.output)

if __name__ == "__main__":
    main()
