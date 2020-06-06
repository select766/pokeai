from pokeai.ai.generic_move_model.agent import Agent


class AgentVal(Agent):
    def __init__(self, model, feature_extractor):
        super().__init__(model, feature_extractor)

    def act(self, obs: object, reward: float) -> int:
        obs_vector, action_mask = self._feature_extractor.transform(obs)
        action = self._act_by_model(obs_vector, action_mask)
        return action

    def stop_episode(self, reward: float) -> None:
        pass
