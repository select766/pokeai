# -*- coding:utf-8 -*-

import sys
import os
import json
import bottle

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
import pokeai_simu
import serializer

field = None


@bottle.route("/make_party")
@bottle.view("make_party")
def make_party():
    return {}


@bottle.route("/make_party", method="POST")
def make_party_post():
    global field
    import test_helper
    parties = test_helper.get_sample_parties()
    field = pokeai_simu.Field(parties)
    field.rng = pokeai_simu.BattleRngRandom(seed=1)
    field.logger = pokeai_simu.FieldLoggerBuffer()
    return bottle.redirect("/battle")


@bottle.route("/battle")
@bottle.view("battle")
def battle():
    return {}


@bottle.route("/field")
def get_field():
    return serializer.serialize_field(field)


@bottle.route("/js_enum/<name>")
def js_enum(name):
    # name={name:value}
    enum_class = getattr(pokeai_simu, name)
    json_obj = {item.name: item.value for item in enum_class}
    js_str = "{}={};".format(name, json.dumps(json_obj))
    return js_str


@bottle.route("/do_step", method="POST")
def do_step():
    print(bottle.request.json)
    req_obj = bottle.request.json
    if field.phase is pokeai_simu.FieldPhase.Begin:
        # アクションをパースして代入
        #["0,Move,2","1,Change,0"]
        actions_begin = []
        for player in [0, 1]:
            action_data = req_obj["selected_actions"][player].split(',')
            if action_data[1] == 'Move':
                actions_begin.append(
                    pokeai_simu.FieldActionBegin.move(int(action_data[2])))
            else:
                actions_begin.append(
                    pokeai_simu.FieldActionBegin.change(int(action_data[2])))
        field.set_actions_begin(actions_begin)
    if field.phase is pokeai_simu.FieldPhase.FaintChange:
        # 倒れた側のみアクションの代入
        actions_faint_change = []
        for player in [0, 1]:
            if field._get_fighting_poke(player).is_faint:
                action_data = req_obj["selected_actions"][player].split(',')
                actions_faint_change.append(
                    pokeai_simu.FieldActionFaintChange(int(action_data[2])))
            else:
                actions_faint_change.append(None)

        field.set_actions_faint_change(actions_faint_change)
    field.step()
    return {}


@bottle.route('/static/<filepath:path>', name='static_file')
def static(filepath):
    return bottle.static_file(filepath, root="./static")


if __name__ == '__main__':
    bottle.run(host="0.0.0.0", port=1511)
