"""
Multidimensional Elo
以下の論文に掲載されたアルゴリズムを実装する。
Re-evaluating evaluation
David Balduzzi, Karl Tuyls, Julien Perolat, Thore Graepel
NeurIPS 2018
http://arxiv.org/abs/1806.02643
"""

import numpy as np

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))

class MElo:
    r: np.ndarray
    c: np.ndarray

    def __init__(self, n_agents: int, c_dim: int, lr: float=1e-3):
        assert n_agents > 1
        assert n_agents > c_dim
        assert c_dim % 2 == 0
        self.n_agents = n_agents
        self.c_dim = c_dim
        self.r = np.zeros(n_agents)
        self.c = self._make_initial_c(n_agents, c_dim)
        self.lr = lr
    
    def _make_initial_c(self, n_agents: int, c_dim: int):
        # cの初期値を生成
        # n_agents * c_dimの行列
        # 論文ではc_dim * n_agentsだが、実装例では転置されているため転置型で実装
        # 各列は、他の列およびすべて1のベクトルと直交する必要がある
        # 乱数で生成したのち、シュミットの直交化法を使って直交化
        c = np.random.randn(c_dim + 1, n_agents)
        c[0] = 1.0 / np.sqrt(n_agents)
        for i in range(1, c_dim + 1):
            for j in range(i):
                c[i] -= np.dot(c[i], c[j]) * c[j]
            c[i] /= np.linalg.norm(c[i])
        return c[1:].T.copy() * 30.0

    def predict(self, i: int, j: int) -> float:
        # エージェントiがエージェントjに勝つ確率を返す
        logit = self.r[i] - self.r[j]
        c = self.c
        for d in range(self.c_dim // 2):
            d0 = d * 2
            d1 = d0 + 1
            logit += c[i, d0] * c[j, d1] - c[i, d1] * c[j, d0]
        return _sigmoid(logit)
    
    def update(self, i: int, j: int, p_ij: float):
        """
        エージェントiとエージェントjの結果p_ijを使ってパラメータを更新
        p_ij: エージェントiがエージェントjに勝つ確率(対戦1回の結果の場合は0または1)
        """
        p_hat_ij = self.predict(i, j)
        delta = (p_ij - p_hat_ij) * self.lr
        self.r[i] += 16 * delta
        self.r[j] -= 16 * delta
        c = self.c
        for d in range(self.c_dim // 2):
            d0 = d * 2
            d1 = d0 + 1
            diffi0 = delta * c[j, d1]
            diffi1 = -delta * c[j, d0]
            diffj0 = -delta * c[i, d1]
            diffj1 = delta * c[i, d0]
            c[i, d0] += diffi0
            c[i, d1] += diffi1
            c[j, d0] += diffj0
            c[j, d1] += diffj1
