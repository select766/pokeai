from typing import Union

from bson import ObjectId

from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc


def load_agent(agent_doc: AgentDoc):
    """
    AgentコレクションのドキュメントからParty, Policyをロードする
    :param agent_doc:
    :return:
    """
    policy = unpack_obj(agent_doc['policy_packed'])
    party = col_party.find_one({'_id': agent_doc['party_id']})['party']
    return party, policy


def load_agent_by_id(_id: Union[ObjectId, str]):
    if not isinstance(_id, ObjectId):
        _id = ObjectId(_id)
    agent_doc = col_agent.find_one({'_id': _id})
    return load_agent(agent_doc)
