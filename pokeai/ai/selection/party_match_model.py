"""
パーティの対戦結果予測モデル
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# パーティの特徴抽出モデル
class PartyMatchFeatModel(nn.Module):
    def __init__(self, num_embeddings: int, output_dim: int):
        # 入力をembeddingし、それをpoolする
        super(PartyMatchFeatModel, self).__init__()
        self.embedding = nn.Embedding(num_embeddings, output_dim)

    def forward(self, x):
        # x: [batch_size, 5]
        # feat: [batch_size, output_dim]
        feat = self.embedding(x)
        feat = torch.mean(feat, dim=1)
        return feat

# パーティの勝敗予測モデル
class PartyMatchPayoffModel(nn.Module):
    def __init__(self, input_dim: int, n_layers: int, hidden_dim: int):
        super(PartyMatchPayoffModel, self).__init__()
        layers = []
        # 最初の次元は、入力特徴をconcatするので2倍
        dim = input_dim * 2
        for i in range(n_layers - 1):
            layers.append(nn.Linear(dim, hidden_dim))
            layers.append(nn.ReLU())
            dim = hidden_dim
        layers.append(nn.Linear(dim, 1))
        self.backbone = nn.Sequential(*layers)

    def forward(self, x, y):
        # x: [batch_size, input_dim]
        # y: [batch_size, input_dim]
        # パーティxの、パーティyに対する利得を予測
        # 反対称性をもつようにする(forward(x,y) = -forward(y,x))
        value_pos = self._forward_backbone(x, y)
        value_neg = self._forward_backbone(y, x)
        value = value_pos - value_neg
        # value: [batch_size]
        # 予測値を[-1, 1]に変換
        payoff = torch.tanh(value)
        return payoff
    
    def _forward_backbone(self, x, y):
        # x: [batch_size, input_dim]
        # y: [batch_size, input_dim]
        # value: [batch_size]
        # 2つのパーティの特徴量を結合
        feat = torch.cat([x, y], dim=1)
        h = self.backbone(feat)
        # 1次元にする
        h = h.view(-1)
        return h

class PartyMatchModel(nn.Module):
    def __init__(self, embed_dim: int = 128, mlp_layers: int = 3, mlp_hidden_dim: int = 64):
        super(PartyMatchModel, self).__init__()
        # 181はポケモン+技の数（本当はメタデータを取得したい）
        self.feat_model = PartyMatchFeatModel(num_embeddings=181, output_dim=embed_dim)
        self.payoff_model = PartyMatchPayoffModel(input_dim=embed_dim, n_layers=mlp_layers, hidden_dim=mlp_hidden_dim)
    
    def forward(self, x, y):
        # x: [batch_size, 5]
        # y: [batch_size, 5]
        # feat_x: [batch_size, embed_dim]
        # feat_y: [batch_size, embed_dim]
        feat_x = self.feat_model(x)
        feat_y = self.feat_model(y)
        # payoff: [batch_size]
        payoff = self.payoff_model(feat_x, feat_y)
        return payoff

    def get_feat(self, x):
        # x: [batch_size, 5]
        # feat_x: [batch_size, embed_dim]
        feat_x = self.feat_model(x)
        return feat_x
