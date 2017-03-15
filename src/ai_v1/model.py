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
    def __init__(self):
        super().__init__(
            fc1=L.Linear(16, 10),
            fc2=L.Linear(10, 4)
        )
    
    def __call__(self, x, test=False):
        h = x
        h = F.relu(self.fc1(h))
        h = self.fc2(h)
        return chainerrl.action_value.DiscreteActionValue(h)
