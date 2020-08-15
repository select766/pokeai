# https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html#dqn-algorithm
import math

import numpy as np

import torch
import torch.optim as optim
import torch.nn.functional as F
from pokeai.ai.generic_move_model.agent_train import AgentTrain
from pokeai.ai.generic_move_model.agent_val import AgentVal
from pokeai.ai.generic_move_model.feature_extractor import FeatureExtractor
from pokeai.ai.generic_move_model.mlp_model import MLPModel
from pokeai.ai.generic_move_model.replay_buffer import ReplayBuffer

DQN_DEFAULT_PARAMS = {
    "epsilon": 0.3,
    "epsilon_decay": 0.0,  # ex. 1e-6 (1 - epsilon_decay) ** step * epsilon
    "gamma": 0.95,
    "batch_size": 32,
    "first_update_steps": 500,
    "optimize_per_steps": 1,
    "target_update": 100,
    "double_dqn": True,
    "replay_buffer_size": 100000,
    "lr": 1e-3,
}


class Trainer:
    def __init__(self, model_params: dict, dqn_params: dict, feature_params: dict):
        self.constructor_params = {
            "model_params": model_params,
            "dqn_params": dqn_params,
            "feature_params": feature_params,
        }
        self.feature_extractor = FeatureExtractor(**feature_params)
        self.model_params = model_params.copy()
        self.model_params["input_shape"] = self.feature_extractor.input_shape
        self.model_params["output_dim"] = self.feature_extractor.output_dim
        self.model = self._construct_model()
        self.target_model = self._construct_model()
        self.target_model.load_state_dict(self.model.state_dict())
        # replay bufferに追加された全ステップ数
        self.total_steps = 0
        # 学習済みステップ数
        self.update_steps = 0
        # DQNの設定
        dqn_params_with_default = DQN_DEFAULT_PARAMS.copy()
        dqn_params_with_default.update(dqn_params)

        self.optimizer = optim.Adam(self.model.parameters(), lr=dqn_params_with_default["lr"])

        self.replay_buffer = ReplayBuffer(dqn_params_with_default["replay_buffer_size"])
        self.epsilon = dqn_params_with_default["epsilon"]
        self.epsilon_decay = dqn_params_with_default["epsilon_decay"]
        self.gamma = dqn_params_with_default["gamma"]
        self.batch_size = dqn_params_with_default["batch_size"]
        self.first_update_steps = dqn_params_with_default["first_update_steps"]
        self.optimize_per_steps = dqn_params_with_default["optimize_per_steps"]  # step回数ごとにoptimizeする
        self.target_update = dqn_params_with_default["target_update"]  # optimize回数ごとにtarget networkをupdate
        self.double_dqn = dqn_params_with_default["double_dqn"]

    def _construct_model(self):
        # TODO: モデルクラスの選択
        return MLPModel(**self.model_params)

    def save_state(self, resume=False):
        # 現状、get_val_agentが可能な最低限の情報を保存している
        # TODO: optimizer, replay_bufferなども保存し、学習の再開も可能とする
        assert resume is False
        return {
            "model": self.model.state_dict(),
            "constructor_params": self.constructor_params,
            "update_steps": self.update_steps
        }

    @classmethod
    def load_state(cls, state):
        trainer = cls(**state["constructor_params"])
        trainer.model.load_state_dict(state["model"])
        return trainer

    def load_initial_model(self, state_dict):
        self.model.load_state_dict(state_dict)
        self.target_model.load_state_dict(state_dict)

    def get_train_agent(self):
        model = self._construct_model()
        model.load_state_dict(self.model.state_dict())
        model.eval()
        epsilon = math.pow(1.0 - self.epsilon_decay, self.total_steps) * self.epsilon
        return AgentTrain(model, self.feature_extractor, epsilon)

    def get_val_agent(self):
        model = self._construct_model()
        model.load_state_dict(self.model.state_dict())
        model.eval()
        return AgentVal(model, self.feature_extractor)

    def extend_replay_buffer(self, buffer: ReplayBuffer):
        steps = len(buffer)
        self.total_steps += steps
        self.replay_buffer.extend(buffer.buffer)

    def train(self):
        while self.update_steps < self.total_steps:
            update_step = self.update_steps
            if update_step % self.optimize_per_steps == 0 and update_step >= self.first_update_steps:
                # update
                self._update()
            if update_step % (self.optimize_per_steps * self.target_update) == 0:
                # target update
                self._target_update()
            self.update_steps += 1

    def _update(self):
        transitions = self.replay_buffer.sample(self.batch_size)
        b_state, b_action_mask, b_action, b_next_state, b_next_action_mask, b_reward = zip(*transitions)
        non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                                b_next_state)), dtype=torch.bool)
        non_final_next_states = torch.from_numpy(np.stack([s for s in b_next_state
                                                           if s is not None]))

        state_batch = torch.from_numpy(np.stack(b_state))
        action_batch = torch.from_numpy(np.array(b_action, dtype=np.int64)[:, np.newaxis])
        reward_batch = torch.from_numpy(np.array(b_reward, dtype=np.float32))
        state_action_values = self.model(state_batch).gather(1, action_batch)
        next_state_values = torch.zeros(self.batch_size)
        # 次のstateの最大action valueを合法手のみから求める
        # 非合法手に対応するaction valueに-infを加算
        non_final_next_action_mask = np.stack([s for s in b_next_action_mask
                                               if s is not None])
        non_final_next_states_bias = torch.from_numpy(
            np.where(non_final_next_action_mask, 0.0, -np.inf).astype(np.float32))
        if self.double_dqn:
            # Double DQN
            # next_stateでのmodelが最大Q値をとるactionを求め、そのQ値をtarget_modelで求める
            next_action = (self.model(non_final_next_states) + non_final_next_states_bias).max(1)[1].detach()
            next_q_target = self.target_model(non_final_next_states).gather(1,
                                                                            next_action.unsqueeze(1)).squeeze().detach()
            next_state_values[non_final_mask] = next_q_target
        else:
            # plain DQN
            # next_stateにおける最大Q値をtarget_modelで求める
            next_state_values[non_final_mask] = \
                (self.target_model(non_final_next_states) + non_final_next_states_bias).max(1)[0].detach()
        # Compute the expected Q values
        expected_state_action_values = (next_state_values * self.gamma) + reward_batch

        # Compute Huber loss
        loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        for param in self.model.parameters():
            param.grad.data.clamp_(-1, 1)
        self.optimizer.step()

    def _target_update(self):
        self.target_model.load_state_dict(self.model.state_dict())
