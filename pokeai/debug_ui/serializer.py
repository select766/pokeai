# -*- coding:utf-8 -*-

import json
import pokeai_simu


def serialize_field(field):
    obj = {}
    obj["parties"] = [serialize_party(party) for party in field.parties]
    obj["phase"] = field.phase.name
    obj["log"] = [str(log_entry) for log_entry in field.logger.buffer]

    return obj


def serialize_party(party):
    obj = {"fighting_poke_idx": party.fighting_poke_idx}
    obj["pokes"] = [serialize_poke(poke) for poke in party.pokes]
    return obj


def serialize_poke(poke):
    st = poke.static_param
    obj = {"static_param":
           {"dexno": st.dexno.name,
            "move_ids": [item.name for item in st.move_ids],
            "type1": st.type1.value,
            "type2": st.type2.value,
            "max_hp": st.max_hp,
            "st_a": st.st_a,
            "st_b": st.st_b,
            "st_c": st.st_c,
            "st_s": st.st_s,
            "base_s": st.base_s,
            "level": st.level}}
    obj["hp"] = poke.hp
    obj["rank_a"] = poke.rank_a
    obj["rank_b"] = poke.rank_b
    obj["rank_c"] = poke.rank_c
    obj["rank_s"] = poke.rank_s
    obj["rank_accuracy"] = poke.rank_accuracy
    obj["rank_evasion"] = poke.rank_evasion
    obj["confusion_turn"] = poke.confusion_turn
    obj["nv_condition"] = poke.nv_condition.name
    obj["sleep_turn"] = poke.sleep_turn
    obj["bad_poison"] = poke.bad_poison
    obj["bad_poison_turn"] = poke.bad_poison_turn
    obj["reflect"] = poke.reflect
    if poke.move_handler is not None:
        obj["move_handler"] = poke.move_handler.move_entry.move_id.name
    else:
        obj["move_handler"] = None

    return obj
