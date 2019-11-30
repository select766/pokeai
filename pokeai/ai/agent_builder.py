"""
jsonで記述可能なエージェント・モデルパラメータからchainerrlのagentクラスのインスタンスを生成
"""
import chainer
from chainerrl.agent import Agent
from chainerrl.agents import A3C
from chainerrl.agents.a3c import A3CSeparateModel
from chainerrl.v_functions import FCVFunction

from pokeai.ai.limited_policy import FCSoftmaxPolicyLimited


def build_agent(params, feature_dims: int, party_size: int) -> Agent:
    if params["version"] == 1:
        return build_agent_v1(params, feature_dims, party_size)
    else:
        raise ValueError("Unknown agent version")


def _get_nested(d: dict, key: str, default: object):
    keys = key.split('.')
    while len(keys) > 0:
        if keys[0] in d:
            d = d[keys[0]]
            keys.pop(0)
        else:
            return default
    return d


def build_agent_v1(params, feature_dims: int, party_size: int) -> Agent:
    model = A3CSeparateModel(
        pi=FCSoftmaxPolicyLimited(feature_dims, party_size * 6, **_get_nested(params, 'model.pi.kwargs', {})),
        v=FCVFunction(feature_dims, **_get_nested(params, 'model.v.kwargs', {})))
    optimizer = chainer.optimizers.Adam(**_get_nested(params, 'optimizer.kwargs', {}))
    optimizer.setup(model)
    if decay := _get_nested(params, 'optimizer.decay', 0.0) > 0.0:
        optimizer.add_hook(chainer.optimizer.WeightDecay(decay))
    # 1バトルはせいぜい100ターンなので、t_maxは大きくして1バトル1回学習ということにする(最後にしか報酬が出ないので)
    agent = A3C(model=model, optimizer=optimizer, t_max=1000, **_get_nested(params, 'agent.kwargs', {}))
    agent.process_idx = 0  # なぜかconstructorで設定されない。バグ？
    return agent


"""
paramsの例

version: 1
model:
    pi:
        kwargs:
            n_hidden_layers: 2
            n_hidden_channels: 32
    v:
        kwargs:
            n_hidden_layers: 1
            n_hidden_channels: 64
optimizer:
    kwargs:
        eps: 1.0e-3
agent:
    kwargs:
        gamma: 1.0
"""
