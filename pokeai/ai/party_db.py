from typing import List, Optional, TypedDict, Dict
import os
import pickle
import gzip
from pymongo import MongoClient
from bson import ObjectId

from pokeai.sim.party_generator import Party

client = MongoClient()
db = client[os.environ.get("POKEAI_PARTY_DB_NAME", "pokeai_3")]
col_party = db["Party"]  # document type PartyDoc
col_trainer = db["Trainer"]  # document type TrainerDoc
col_rate = db["Rate"]  # document type RateDoc


class PartyDoc(TypedDict):
    _id: ObjectId
    party: Party
    tags: List[str]


class TrainerDoc(TypedDict):
    _id: ObjectId
    trainer_packed: bytes  # pack_obj(Trainer.save_state())
    train_params: dict  # 学習手法パラメータ
    tags: List[str]


class RateDoc(TypedDict):
    _id: ObjectId
    rates: Dict[str, float]  # str(trainer_id)+'+'+str(party_id) => rate (平均1500)


def pack_obj(obj):
    return gzip.compress(pickle.dumps(obj))


def unpack_obj(b: bytes):
    return pickle.loads(gzip.decompress(b))
