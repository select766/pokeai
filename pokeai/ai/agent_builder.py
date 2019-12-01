"""
jsonで記述可能なエージェント・モデルパラメータからchainerrlのagentクラスのインスタンスを生成
"""
import chainer
from chainer.optimizer_hooks import WeightDecay
from chainerrl.agent import Agent
from chainerrl.agents import A3C
from chainerrl.agents.a3c import A3CSeparateModel
from chainerrl.agents.acer import ACERSeparateModel, ACER
from chainerrl.q_functions import FCStateQFunctionWithDiscreteAction
from chainerrl.replay_buffer import EpisodicReplayBuffer
from chainerrl.v_functions import FCVFunction

from pokeai.ai.limited_policy import FCSoftmaxPolicyLimited


def build_agent(params, feature_dims: int, party_size: int) -> Agent:
    if params["version"] == 1:
        return build_agent_v1(params, feature_dims, party_size)
    elif params["version"] == 2:
        return build_agent_v2(params, feature_dims, party_size)
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


def build_agent_v2(params, feature_dims: int, party_size: int) -> Agent:
    model_type = _get_nested(params, 'model.type', None)
    if model_type == 'ACERSeparateModel':
        model = ACERSeparateModel(
            pi=FCSoftmaxPolicyLimited(feature_dims, party_size * 6, **_get_nested(params, 'model.pi.kwargs', {})),
            q=FCStateQFunctionWithDiscreteAction(feature_dims, party_size * 6,
                                                 **_get_nested(params, 'model.q.kwargs', {})))
    elif model_type == 'A3CSeparateModel':
        model = A3CSeparateModel(
            pi=FCSoftmaxPolicyLimited(feature_dims, party_size * 6, **_get_nested(params, 'model.pi.kwargs', {})),
            v=FCVFunction(feature_dims, **_get_nested(params, 'model.v.kwargs', {})))
    else:
        raise ValueError(f"Unknown model type {model_type}")
    optimizer = chainer.optimizers.Adam(**_get_nested(params, 'optimizer.kwargs', {}))
    optimizer.setup(model)
    if decay := _get_nested(params, 'optimizer.decay', 0.0) > 0.0:
        for param in model.params():
            if param.name != 'b':  # バイアス以外だったら
                param.update_rule.add_hook(WeightDecay(decay))  # 重み減衰を適用
    agent_type = _get_nested(params, 'agent.type', None)
    if agent_type == 'ACER':
        replay_buffer = EpisodicReplayBuffer(**_get_nested(params, 'replay_buffer.kwargs', {}))
        agent = ACER(model=model, optimizer=optimizer, t_max=1000, replay_buffer=replay_buffer,
                     **_get_nested(params, 'agent.kwargs', {}))
        agent.process_idx = 0
    elif agent_type == 'A3C':
        # 1バトルはせいぜい100ターンなので、t_maxは大きくして1バトル1回学習ということにする(最後にしか報酬が出ないので)
        agent = A3C(model=model, optimizer=optimizer, t_max=1000, **_get_nested(params, 'agent.kwargs', {}))
        agent.process_idx = 0  # なぜかconstructorで設定されない。バグ？
    else:
        raise ValueError(f"Unknown agent type {agent_type}")

    return agent


"""
paramsの例

version: 2
model:
    type: ACERSeparateModel
    pi:
        kwargs:
            n_hidden_layers: 2
            n_hidden_channels: 32
    q:
        kwargs:
            n_hidden_layers: 1
            n_hidden_channels: 64
optimizer:
    kwargs:
        eps: 1.0e-3
agent:
    type: ACER
    kwargs:
        gamma: 1.0
        replay_start_size: 100
replay_buffer:
    kwargs:
        capacity: 1000
"""
