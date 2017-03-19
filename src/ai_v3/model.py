# -*- coding:utf-8 -*-

import sys
import os
import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import numpy as np
import gym
import gym.spaces

class QFunction(chainer.Chain):
    def __init__(self, n_obs, n_action, n_hidden=32):
        super().__init__(
            fc1=L.Linear(n_obs, n_hidden),
            bn1=L.BatchNormalization(n_hidden),
            fc2=L.Linear(n_hidden, n_action)
        )
        self.n_action = n_action
    
    def __call__(self, x, test=False):
        h = x
        h = F.relu(self.fc1(h))
        possible_action, _ = F.split_axis(x, [self.n_action], axis=1)
        h = self.fc2(h)
        h = h + (possible_action - 1.0) * 10.0
        return chainerrl.action_value.DiscreteActionValue(h)

class QFunctionShallow(chainer.Chain):
    def __init__(self, n_obs, n_action):
        super().__init__(
            fc1=L.Linear(n_obs, n_action)
        )
        self.n_action = n_action
    
    def __call__(self, x, test=False):
        h = x
        h = self.fc1(h)
        return chainerrl.action_value.DiscreteActionValue(h)
