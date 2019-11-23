from typing import List, Optional, TypedDict, Dict
import os
import pickle
import gzip
from pymongo import MongoClient
from bson import ObjectId

from pokeai.sim.party_generator import Party

client = MongoClient()
db = client[os.environ.get("POKEAI_PARTY_DB_NAME", "pokeai_2")]
col_party = db["Party"]  # document type PartyDoc
col_agent = db["Agent"]  # document type AgentDoc
col_rate = db["Rate"]  # document type RateDoc


class PartyDoc(TypedDict):
    _id: ObjectId
    party: Party
    tags: List[str]


class AgentDoc(TypedDict):
    _id: ObjectId
    party_id: ObjectId
    policy_packed: bytes  # pack_objによりシリアライズされたActionPolicy
    tags: List[str]


class RateDoc(TypedDict):
    _id: ObjectId
    rates: Dict[str, float]  # str(agent_id) => rate (平均1500)


def pack_obj(obj):
    return gzip.compress(pickle.dumps(obj))


def unpack_obj(b: bytes):
    return pickle.loads(gzip.decompress(b))
