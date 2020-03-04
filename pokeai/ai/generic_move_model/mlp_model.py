import torch.nn as nn
import torch.nn.functional as F


class MLPModel(nn.Module):
    def __init__(self, input_dim, n_layers=2, n_channels=64, bn=False):
        super().__init__()
        layers = []
        bn_layers = []
        cur_hidden_ch = input_dim
        for i in range(n_layers):
            layers.append(nn.Conv1d(cur_hidden_ch, n_channels, 1, bias=not bn))  # in,out,ksize
            cur_hidden_ch = n_channels
            if bn:
                bn_layers.append(nn.BatchNorm1d(n_channels))
        self.layers = nn.ModuleList(layers)
        self.bn_layers = nn.ModuleList(bn_layers)
        self.output = nn.Conv1d(cur_hidden_ch, 1, 1)
        self.bn = bn

    def forward(self, x):
        h = x  # batch, feature_dim, 4
        for i in range(len(self.layers)):
            h = self.layers[i](h)
            if self.bn:
                h = self.bn_layers[i](h)
            h = F.relu(h)
        h = self.output(h)
        h = h.view(h.shape[0], -1)  # batch, 4
        return h
