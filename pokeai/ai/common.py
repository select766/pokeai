from typing import Union, List, Tuple

from bson import ObjectId
import numpy as np

from pokeai.ai.battle_status import BattleStatus
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from pokeai.sim.party_generator import Party
from pokeai.ai.dex import dex


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


def get_possible_actions(battle_status: BattleStatus, request: dict) -> Tuple[List[int], List[str], np.ndarray]:
    """
    取れる行動の番号およびそれを表す文字列を返す
    :param battle_status: プレイヤー側のバトル状態
    :param request: シミュレータからのrequestオブジェクト
    :return:
    """

    """
    出力ベクトルの各次元と行動の関係
    X番目のポケモン(X=0~5)
    6X+0~3: 技0~3
    6X+4: このポケモンに交代
    6X+5: 強制交換の時このポケモンを出す
    """
    force_switch = bool(request.get("forceSwitch"))
    active_poke_idx = None
    choice_idxs = []
    choice_keys = []
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

    # request['side']['pokemon']:
    # {\"ident\":\"p1: Kangaskhan\",\"details\":\"Kangaskhan, L50, F\",\"condition\":\"211/211\",\"active\":true,
    # \"stats\":{\"atk\":146,\"def\":131,\"spa\":91,\"spd\":131,\"spe\":141},\"moves\":[\"thunder\",\"return102\",
    # \"thunderbolt\",\"rest\"],\"baseAbility\":\"noability\",\"item\":\"\",\"pokeball\":\"pokeball\"},
    # {\"ident\":\"p1: Lapras\",...
    # 今出ているポケモンが先頭になっている（ゲーム内の交換画面と同様）ことに注意。
    # モデルの出力行動番号はパーティ構築上の順序に変換する必要がある
    species_to_party_idx = {}  # パーティ構築における、ポケモンの名前とインデックスの対応
    for i, party_poke in enumerate(battle_status.side_party):
        species_to_party_idx[party_poke['species']] = i
    for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
        # FIXME: 種族名が得られるが、ニックネームついてると違うかも？
        pokemon_name = backpokemon['ident'][4:]  # "p1: Kangaskhan" => "Kangaskhan"
        pokemon_id = dex.get_pokedex_by_name(pokemon_name)['id']  # "Kangaskhan"=>"kangaskhan"
        party_idx = species_to_party_idx[pokemon_id]
        if backpokemon['active']:
            # 場に出ている
            active_poke_idx = party_idx
            continue
        if backpokemon['condition'].endswith(' fnt'):
            # 瀕死状態
            continue
        if not trapped:
            if force_switch:
                choice_idxs.append(party_idx * 6 + 5)  # どのポケモンに交換するかのモデル上では、パーティ構築上のインデックスを利用
                choice_keys.append(f'switch {i + 1}')  # 1-origin index、パーティ構築ではなく今出ているポケモンを先頭としたインデックスで指定
            else:
                choice_idxs.append(party_idx * 6 + 4)
                choice_keys.append(f'switch {i + 1}')
    assert active_poke_idx is not None
    if not force_switch:
        for i, move in enumerate(active[0]['moves']):
            if not move.get('disabled'):
                choice_idxs.append(active_poke_idx * 6 + i)
                choice_keys.append(f'move {i + 1}')  # 1-origin index
    assert len(choice_idxs) > 0
    vec = np.zeros((len(request['side']['pokemon']) * 6,), dtype=np.float32)
    vec[choice_idxs] = 1.0
    return choice_idxs, choice_keys, vec
