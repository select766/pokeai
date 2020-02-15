import torch.nn as nn
import torch.nn.functional as F


class MLPModel(nn.Module):
    def __init__(self, input_dim, n_layers=2, n_channels=64):
        super().__init__()
        layers = []
        layers.append(nn.Conv1d(input_dim, n_channels, 1))  # in,out,ksize
        for i in range(n_layers):
            layers.append(nn.Conv1d(n_channels, n_channels, 1))
        self.layers = nn.ModuleList(layers)
        self.output = nn.Conv1d(n_channels, 1, 1)

    def forward(self, x):
        h = x  # batch, feature_dim, 4
        for i in range(len(self.layers)):
            h = F.relu(self.layers[i](h))
        h = self.output(h)
        h = h.view(h.shape[0], -1)  # batch, 4
        return h
