from typing import List, Optional
import os
import pickle

from pokeai.sim.party_template import PartyTemplate
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient()
db = client[os.environ["POKEAI_PARTY_DB_NAME"]]
col_party = db["Party"]
col_party_group = db["PartyGroup"]
col_agent = db["Agent"]
col_rate = db["Rate"]


def save_party_template(party_t: PartyTemplate):
    s_party = pickle.dumps(party_t, protocol=pickle.HIGHEST_PROTOCOL)
    col_party.insert_one({"_id": party_t.party_id, "party_template": s_party})


def load_party_template(_id: ObjectId) -> PartyTemplate:
    obj = col_party.find_one({"_id": _id})
    if obj is None:
        raise KeyError
    party_t = pickle.loads(obj["party_template"])
    assert _id == party_t.party_id
    return party_t


def save_party_group(party_t_list: List[PartyTemplate], tag: Optional[str] = None) -> ObjectId:
    """
    パーティおよびグループ情報を保存する
    :param party_t_list:
    :param tag: グループのtag(名称)
    :return: グループid
    """
    group_id = ObjectId()
    tags = [str(group_id)]  # group_idの文字列もtagとしてグループを指すのに使える
    if tag:
        if col_party_group.find_one({"tags": tag}) is not None:
            raise KeyError(f"tag {tag} already exists")
        tags.append(tag)
    ids = []
    for party_t in party_t_list:
        save_party_template(party_t)
        ids.append(party_t.party_id)
    group_data = {"_id": group_id, "party_ids": ids, "tags": tags}
    col_party_group.insert_one(group_data)
    return group_id


def load_party_group(tag: str) -> List[PartyTemplate]:
    """
    パーティグループをロードする
    :param tag:
    :return:
    """
    group_data = col_party_group.find_one({"tags": str(tag)})
    if group_data is None:
        raise KeyError
    party_t_list = []
    for party_id in group_data["party_ids"]:
        party_t_list.append(load_party_template(party_id))
    return party_t_list
