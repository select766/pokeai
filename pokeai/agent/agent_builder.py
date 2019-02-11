"""
ChainerRLのエージェントをパラメータ設定から作成する
"""
import chainer.optimizers
import chainerrl

from pokeai.agent.battle_observer import BattleObserver

q_function_classes = {
    "FCStateQFunctionWithDiscreteAction": chainerrl.q_functions.FCStateQFunctionWithDiscreteAction,
}

optimizer_classes = {
    "MomentumSGD": chainer.optimizers.MomentumSGD,
    "Adam": chainer.optimizers.Adam
}

explorer_classes = {
    "ConstantEpsilonGreedy": chainerrl.explorers.ConstantEpsilonGreedy
}

agent_classes = {
    "DQN": chainerrl.agents.DQN,
    "DoubleDQN": chainerrl.agents.DoubleDQN,
}


def build(params, observer: BattleObserver):
    assert params["version"] == 1  # 将来の拡張に備えバージョン番号を指定することにする
    obs_size = observer.observation_space.shape[0]
    n_actions = observer.action_space.n
    q_func = q_function_classes[params["q_function"]["name"]](obs_size, n_actions,
                                                              **params["q_function"].get("kwargs", {}))

    optimizer = optimizer_classes[params["optimizer"]["name"]](**params["optimizer"].get("kwargs"))
    optimizer.setup(q_func)

    gamma = params["gamma"]

    explorer = explorer_classes[params["explorer"]["name"]](random_action_func=observer.action_space.sample,
                                                            **params["explorer"]["kwargs"])

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(**params["replay_buffer"])

    agent = agent_classes[params["agent"]["name"]](
        q_function=q_func, optimizer=optimizer, replay_buffer=replay_buffer, gamma=gamma,
        explorer=explorer, **params["agent"]["kwargs"])

    return agent
