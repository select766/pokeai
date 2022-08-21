from typing import List, NamedTuple, Optional

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.dex import dex


class PossibleAction(NamedTuple):
    simulator_key: str  # (move [1-4]|switch [1-6]) シミュレータに渡す行動記号
    poke: str  # 技の場合、自分の場に出ているポケモン。交代の場合、交代先のポケモン。
    move: Optional[str]  # 技の場合、技のID。交代の場合、None。
    switch: bool  # 交代の場合True。force_switchのときもTrue
    force_switch: bool  # 瀕死になって強制交代の場合True。
    allMoves: List[str]  # 技の場合自分の場に出ているポケモン/交代の場合交代先ポケモンのすべての技。
    item: str  # 技の場合自分の場に出ているポケモン/交代の場合交代先ポケモンが持っている道具。持っていないとき空文字列。


def rename_special_move_id_active(id: str, name: str) -> str:
    if id == "hiddenpower":
        # name: "Hidden Power Dark 70"
        return "hiddenpower" + name.split(" ")[2].lower()
    return id


def rename_special_move_id_side(id: str) -> str:
    if id.startswith("return"):
        return "return"
    elif id.startswith("frustration"):
        return "frustration"
    return id


def get_possible_actions(request: dict) -> List[PossibleAction]:
    """
    取れる行動を表すオブジェクト列を返す
    :param battle_status: プレイヤー側のバトル状態
    :param request: シミュレータからのrequestオブジェクト
    :return:
    """

    force_switch = bool(request.get("forceSwitch"))
    if not force_switch:
        active = request['active']
        trapped = active[0].get('trapped')  # 交換不可状態
    else:
        active = None
        trapped = False

    # ゴッドバードなど複数ターン継続する技では、
    # [{"moves":[{"move":"Sky Attack","id":"skyattack"}],"trapped":true}],
    # のようにmoveが１要素だけになり、active.trapped:trueとなる
    # moveの番号自体ずれる(固定された技を強制選択となり"move 1"を返すこととなる)ので、番号と技の対応に注意
    # TODO: ソーラービームで"trapped"がないがmoveが1要素だけという事態があり要検証

    # request['side']['pokemon']:
    # {\"ident\":\"p1: Kangaskhan\",\"details\":\"Kangaskhan, L50, F\",\"condition\":\"211/211\",\"active\":true,
    # \"stats\":{\"atk\":146,\"def\":131,\"spa\":91,\"spd\":131,\"spe\":141},\"moves\":[\"thunder\",\"return102\",
    # \"thunderbolt\",\"rest\"],\"baseAbility\":\"noability\",\"item\":\"\",\"pokeball\":\"pokeball\"},
    # {\"ident\":\"p1: Lapras\",...
    # 今出ているポケモンが先頭になっている（ゲーム内の交換画面と同様）ことに注意。

    # めざめるパワー、おんがえし、やつあたりについて
    # {
    #     "active": [
    #         {
    #             "moves": [
    #                 {
    #                     "move": "Return 102",
    #                     "id": "return",
    #                     "pp": 32,
    #                     "maxpp": 32,
    #                     "target": "normal",
    #                     "disabled": false
    #                 },
    #                 {
    #                     "move": "Hidden Power Dark 70",
    #                     "id": "hiddenpower",
    #                     "pp": 24,
    #                     "maxpp": 24,
    #                     "target": "normal",
    #                     "disabled": false
    #                 },
    #                 {
    #                     "move": "Frustration 1",
    #                     "id": "frustration",
    #                     "pp": 29,
    #                     "maxpp": 32,
    #                     "target": "normal",
    #                     "disabled": false
    #                 },
    #                 {
    #                     "move": "Giga Drain",
    #                     "id": "gigadrain",
    #                     "pp": 8,
    #                     "maxpp": 8,
    #                     "target": "normal",
    #                     "disabled": false
    #                 }
    #             ]
    #         }
    #     ],
    #     "side": {
    #         "name": "p1",
    #         "id": "p1",
    #         "pokemon": [
    #             {
    #                 "ident": "p1: Ledian",
    #                 "details": "Ledian, L55, M",
    #                 "condition": "52/176",
    #                 "active": true,
    #                 "stats": {
    #                     "atk": 94,
    #                     "def": 111,
    #                     "spa": 116,
    #                     "spd": 177,
    #                     "spe": 149
    #                 },
    #                 "moves": [
    #                     "return102",
    #                     "hiddenpowerdark",
    #                     "frustration1",
    #                     "gigadrain"
    #                 ],
    #                 "baseAbility": "noability",
    #                 "item": "",
    #                 "pokeball": "pokeball"
    #             }
    #         ]
    #     }
    # }
    # active（場に出ているポケモン）と、side（控えを含めたポケモンリスト）で表記が変化する。
    # return102はおんがえし威力102であることを示している。
    # 本システムではおんがえしは威力102、やつあたりは威力1固定で扱い、"return102"は"return"に書き換える。
    # めざめるパワー(hiddenpower)はタイプが重要なので、タイプが判明する場合はタイプ付きのidに書き換える。
    # 例: "hiddenpower" -> "hiddenpowerdark" ("Hidden Power Dark 70"から情報を得た場合)
    # 判明しない場合がもしあれば"hiddenpower"のままとする。
    # 参考: Pokemon-Showdown/sim/pokemon.ts
    # moveName = 'Return ' + this.battle.getMove('return')!.basePowerCallback(this);
    # Pokemon-Showdown/data/moves.js
    # 		basePowerCallback(pokemon) {
    # 			return Math.floor(((255 - pokemon.happiness) * 10) / 25) || 1;
    # 		},
    possible_actions = []  # type: List[PossibleAction]
    for poke_idx, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
        pokemon_name = backpokemon['details'].split(',')[0]  # "Kangaskhan, L50, F" => "Kangaskhan"
        pokemon_id = dex.get_pokedex_by_name(pokemon_name)['id']  # "Kangaskhan"=>"kangaskhan"
        if backpokemon['active']:
            # 場に出ているポケモン=技の選択
            if not force_switch:
                for move_idx, move in enumerate(active[0]['moves']):
                    if not move.get('disabled'):
                        possible_actions.append(PossibleAction(simulator_key=f'move {move_idx + 1}',
                                                               poke=pokemon_id,
                                                               move=rename_special_move_id_active(move['id'],
                                                                                                  move['move']),
                                                               switch=False,
                                                               force_switch=False,
                                                               allMoves=[rename_special_move_id_side(m) for m in
                                                                         backpokemon['moves']],
                                                               item=backpokemon['item']))
        else:
            # 場に出てないポケモン=交代の選択
            if backpokemon['condition'].endswith(' fnt'):
                # 瀕死状態
                continue
            if trapped:
                continue
            possible_actions.append(PossibleAction(simulator_key=f'switch {poke_idx + 1}',
                                                   poke=pokemon_id,
                                                   move=None,
                                                   switch=True,
                                                   force_switch=force_switch,
                                                   allMoves=[rename_special_move_id_side(m) for m in
                                                             backpokemon['moves']],
                                                   item=backpokemon['item']))
    return possible_actions
