import pickle
import copy
import itertools


class PartyGenerator:
    def __init__(self, friend_parties_path, enemy_parties_path, friend_party_idx):
        with open(friend_parties_path, "rb") as f:
            friend_parties = pickle.load(f)
        self.friend_party = friend_parties[friend_party_idx]  # パーティ群のうち指定インデックスのものを用いる
        with open(enemy_parties_path, "rb") as f:
            enemy_parties = pickle.load(f)
        self.enemy_parties_iter = itertools.cycle(enemy_parties)  # 無限ループでパーティ群を読む

    def __call__(self):
        return [copy.deepcopy(self.friend_party), copy.deepcopy(next(self.enemy_parties_iter))]
