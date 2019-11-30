"""
jsonで記述可能なエージェント・モデルパラメータからchainerrlのagentクラスのインスタンスを生成
"""
import chainer
from chainerrl.agents import A3C
from chainerrl.agents.a3c import A3CSeparateModel
from chainerrl.v_functions import FCVFunction

from pokeai.ai.limited_policy import FCSoftmaxPolicyLimited


def build_agent(params, feature_dims) -> A3C:
    model = A3CSeparateModel(pi=FCSoftmaxPolicyLimited(feature_dims, 18),
                             v=FCVFunction(feature_dims))
    optimizer = chainer.optimizers.Adam(eps=1e-3)
    optimizer.setup(model)
    agent = A3C(model=model, optimizer=optimizer, t_max=1000, gamma=1.0)
    agent.process_idx = 0  # なぜかconstructorで設定されない。バグ？
    return agent
