from pokeai.agent.battle_agent import BattleAgent
from pokeai.agent.battle_agent_random import BattleAgentRandom
from pokeai.agent.battle_agent_rl import BattleAgentRl
from pokeai.agent.battle_observer import BattleObserver
from pokeai.agent import party_db

battle_agents = {
    "BattleAgentRandom": BattleAgentRandom,
    "BattleAgentRl": BattleAgentRl,
}


def load_agent(agent_info) -> BattleAgent:
    # agent_info: {_id: ObjectId, party_id: ObjectId, class_name: str, observer: dict, agent: dict, tags: List[str]}
    agent_class = battle_agents[agent_info["class_name"]]
    observer = BattleObserver(**agent_info["observer"])
    party_t = party_db.load_party_template(agent_info["party_id"])
    agent = agent_class(agent_info["_id"], party_t, observer, **agent_info["agent"])
    return agent
