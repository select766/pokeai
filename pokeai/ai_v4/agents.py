import numpy as np


class RandomAgent:
    """
    ランダムな行動を返すエージェント。交代を選ぶ確率を設定可能。
    """

    def __init__(self, party_size: int, n_moves: int, change_probability: float):
        """
        :param party_size: パーティのサイズ。
        :param n_moves: 技の種類数。
        :param change_probability: 交代を選ぶ確率。0の場合、技が選べれば必ず技を選ぶ。
        """
        self.party_size = party_size
        self.n_moves = n_moves
        self.change_probability = change_probability

    def act(self, obs: np.ndarray) -> int:
        # [技N種類、交代先party_size、ひんし交代先party_size]があると想定。
        party_size = self.party_size
        n_moves = self.n_moves
        move_vec = obs[:n_moves]
        change_vec = obs[n_moves:n_moves + party_size]
        faint_change_vec = obs[n_moves + party_size:n_moves + party_size + party_size]
        can_move = np.any(move_vec)
        can_change = np.any(change_vec)
        can_faint_change = np.any(faint_change_vec)
        if can_faint_change:
            # 瀕死交代
            return np.random.choice(np.flatnonzero(faint_change_vec)) + n_moves + party_size
        else:
            if can_move and can_change:
                # 技と交代両方可能なので、どちらかを選ぶ
                if np.random.random() < self.change_probability:
                    # 交代
                    can_move = False
            if can_move:
                # 技
                return np.random.choice(np.flatnonzero(move_vec))
            else:
                assert can_change
                return np.random.choice(np.flatnonzero(change_vec)) + n_moves
