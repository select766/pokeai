"""
合法手が状況ごとに変化する場合のchainerrl policy関係のクラス
chainerrlのソースコードをもとに改造

"""
import numpy as np
import chainer
from chainer import functions as F
from chainer.initializers import LeCunNormal
from chainer import links as L
from chainerrl.distribution import CategoricalDistribution
from cached_property import cached_property
from chainer import backend
from chainerrl.links.mlp import MLP
from chainerrl.policy import Policy


def _unwrap_variable(x):
    if isinstance(x, chainer.Variable):
        return x.array
    else:
        return x


class SoftmaxDistributionLimited(CategoricalDistribution):
    """Softmax distribution.
    Args:
        logits (ndarray or chainer.Variable): Logits for softmax
            distribution.
        beta (float): inverse of the temperature parameter of softmax
            distribution
    """

    def __init__(self, logits, valids, beta=1.0):
        self.logits = logits
        self.valids = valids
        self.beta = beta
        self.n = logits.shape[1]

    @property
    def params(self):
        return self.logits, self.valids

    @cached_property
    def logits_valid(self):
        # validsを掛け算することで非合法手へのbackpropを防止、F.logで合法手(1)は0加算、非合法手(0)は-10000を加算
        # 十分小さいlogitならexpの計算過程で完全に0となり選ばれないので大丈夫、-infを与えるとnanが発生して厄介
        return self.logits * self.valids + (1.0 - self.valids) * -10000.0

    @cached_property
    def all_prob(self):
        with chainer.force_backprop_mode():
            return F.softmax(self.beta * self.logits_valid)

    @cached_property
    def all_log_prob(self):
        with chainer.force_backprop_mode():
            return F.log_softmax(self.beta * self.logits_valid)

    @cached_property
    def entropy(self):
        with chainer.force_backprop_mode():
            xp = backend.get_array_module(self.logits)
            # 有効な要素のみで計算する
            # return - F.sum(F.where(F.cast(self.valids, np.bool), self.all_prob * self.all_log_prob,
            #                        chainer.Variable(xp.zeros_like(self.logits.data))), axis=1)
            return - F.sum(self.all_prob * self.all_log_prob, axis=1)

    def copy(self):
        return SoftmaxDistributionLimited(_unwrap_variable(self.logits).copy(), _unwrap_variable(self.valids).copy(),
                                          beta=self.beta)

    def __repr__(self):
        return 'SoftmaxDistributionLimited(beta={}) logits:{} valids:{} probs:{} entropy:{}'.format(  # NOQA
            self.beta, self.logits.array, self.valids.array,
            self.all_prob.array, self.entropy.array)

    def __getitem__(self, i):
        return SoftmaxDistributionLimited(self.logits[i], self.valids[i], beta=self.beta)


class FCSoftmaxPolicyLimited(chainer.Chain, Policy):
    """
    合法手制限がある場合に対応したSoftmax policy
    観測ベクトルの先頭にn_actions次元のbinary vectorがついていると仮定
    """

    def __init__(self, n_input_channels, n_actions,
                 n_hidden_layers=0, n_hidden_channels=None,
                 beta=1.0, nonlinearity=F.relu,
                 last_wscale=1.0):
        self.n_input_channels = n_input_channels
        self.n_actions = n_actions
        self.n_hidden_layers = n_hidden_layers
        self.n_hidden_channels = n_hidden_channels
        self.beta = beta

        super().__init__(
            model=MLP(n_input_channels,
                      n_actions,
                      (n_hidden_channels,) * n_hidden_layers,
                      nonlinearity=nonlinearity,
                      last_wscale=last_wscale))

    def __call__(self, x):
        h = self.model(x)
        xp = backend.get_array_module(h)
        return SoftmaxDistributionLimited(
            h, chainer.Variable(xp.asarray(x[:, :self.n_actions])), beta=self.beta)
