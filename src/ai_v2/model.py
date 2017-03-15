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
    def __init__(self, n_obs, n_action):
        super().__init__(
            fc1=L.Linear(n_obs, 32),
            fc2=L.Linear(32, n_action)
        )
    
    def __call__(self, x, test=False):
        h = x
        h = F.relu(self.fc1(h))
        h = self.fc2(h)
        return chainerrl.action_value.DiscreteActionValue(h)
