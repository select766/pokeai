import argparse
import json
import re

from pokeai.util import compress_open

prefix_match_start = "DEBUG:__main__:match start: "
prefix_read_chunk = "DEBUG:pokeai.sim.sim:readChunk "
prefix_read_chunk_update = "DEBUG:pokeai.sim.sim:readChunk \"update"
re_choice_of_player = re.compile("^DEBUG:pokeai.ai.rl_policy:choice of player (p[12])")
prefix_possible_actions = "DEBUG:pokeai.ai.rl_policy:possible_actions: "
prefix_q_func = "DEBUG:pokeai.ai.generic_move_model.agent:q_func: "
prefix_choice_turn_start = "DEBUG:pokeai.sim.battle_stream_processor:choice_turn_start: "
prefix_choice_force_switch = "DEBUG:pokeai.sim.battle_stream_processor:choice_force_switch: "
prefix_read_chunk_end = "DEBUG:pokeai.sim.sim:readChunk \"end"

"""
# 解析すべき行について

## バトル開始
`DEBUG:__main__:match start: {"p1": {"player_id": "5f8277aec93c5fa90a0023b3+5f633609975eefc2110a5ae5", "party": [{"name": "corsola", "species": "corsola", "moves": ["sandstorm", "toxic", "rocksmash", "earthquake"]`
プレイヤーp1, p2のエージェントおよびパーティ情報。`agent_id`は`trainer_id+party_id`形式。

## ターン経過

`DEBUG:pokeai.sim.sim:readChunk "update\\n|`がキー。

```
DEBUG:pokeai.sim.sim:readChunk "update\\n|\\n|move|p1a: Zapdos|Thunderbolt|p2a: Flareon\\n|split|p2\\n|-damage|p2a: Flareon|108/171\\n|-damage|p2a: Flareon|108/171\\n|move|p2a: Flareon|Flamethrower|p1a: Zapdos\\n|split|p1\\n|-damage|p1a: Zapdos|130/196\\n|-damage|p1a: Zapdos|130/196\\n|\\n|upkeep\\n|turn|2"\n
 ```
 
1行に1個出来事がかかれている。

`|split|p2`のような`|split|`で開始する行の次の行は該当プレイヤーのみに知らされるものだが、特に不要っぽいので読み捨てていい。設定によっては全員に見えるメッセージではHPがパーセンテージで、一方のプレイヤーにだけ実数値が見えるとかにできると思われる。

各メッセージのシミュレータの説明`Pokemon-Showdown/sim/SIM-PROTOCOL.md`


## ターン開始時/強制交代発生時の選択
p1の選択に関する情報開始 `DEBUG:pokeai.ai.rl_policy:choice of player p1\n`

選択可能な行動リスト `DEBUG:pokeai.ai.rl_policy:possible_actions: [{"simulator_key": "move 1", "poke": "zapdos",...`

各行動に対するq値と選択した行動（行動リストのindex） `DEBUG:pokeai.ai.generic_move_model.agent:q_func: {"q_func": [-0.08062701672315598, 0.24319157004356384, 0.030384177342057228, -0.03626624122262001, -0.09583178907632828, -0.2755809724330902], "action": 1}\n',`
q値、対応するactionがない場所は`-Infinity`が入っている。pythonではOKだが、jsではJSON.parseでエラーになる。

履歴から再現したバトルの状態（残りHP、対面している相手ポケモンなど） ターン開始時は`DEBUG:pokeai.sim.battle_stream_processor:choice_turn_start: {"battle_status": ...`、強制交代時は`DEBUG:pokeai.sim.battle_stream_processor:choice_force_switch: ...`

## ゲーム終了
endメッセージ。2行目にJSONが入っている。winnerの値が`p1`,`p2`,空文字列(引き分け)となる。 `DEBUG:pokeai.sim.sim:readChunk "end\\n{\\"winner\\":\\"p1\\",...`

# メッセージ順序
- バトル開始
- ターン0経過(最初の対面) `DEBUG:pokeai.sim.sim:readChunk "update\\n|player|p1|p1|...|switch|p1a: Ariados|Ariados, L50, M|176/176\\n...|turn|1"\n`
- ターンN選択
- ターンN経過
  - 強制交代・バトル終了がない場合、updateメッセージの最後に`|turn|N+1`が来る
- 強制交代発生時
  - 該当プレイヤーに選択が発生（倒した反動で技を出したほうも倒れるなど、両方のプレイヤーの場合もありうる。）
  - 強制交代したポケモンを繰り出すターン経過 updateメッセージの最後に`|turn|N+1`が来る
- 終了でない場合ターンN選択に戻る
- ゲーム終了
"""


def extract_json(line, prefix):
    return json.loads(line[len(prefix):])


def parse_battle_status(json_obj):
    return {"battle_status": json.loads(json_obj["battle_status_json"]), "request": json_obj["request"],
            "choice": json_obj["choice"]}


def parse_update(message):
    return message.split("\n")[
           1:]  # ["|","|move|p1a: Beedrill|Sludge Bomb|p2a: Ledian","|split|p2",|-damage|p2a: Ledian|73/161",..."|turn|15"]


def parse_end(message):
    return json.loads(message.split("\n")[1])


def parse_one_battle(f):
    agents_info = None
    choice_info = None
    events = []
    end = None
    while True:
        line = f.readline()
        if not line:
            break
        if line.startswith(prefix_match_start):
            agents_info = extract_json(line, prefix_match_start)
        m = re_choice_of_player.match(line)
        if m:
            player = m.group(1)  # p1/p2
            choice_info = {"player": player}
        if line.startswith(prefix_possible_actions):
            choice_info["possible_actions"] = extract_json(line, prefix_possible_actions)
        if line.startswith(prefix_q_func):
            choice_info["q_func"] = extract_json(line, prefix_q_func)
        bs = None
        if line.startswith(prefix_choice_turn_start):
            bs = parse_battle_status(extract_json(line, prefix_choice_turn_start))
        if line.startswith(prefix_choice_force_switch):
            bs = parse_battle_status(extract_json(line, prefix_choice_force_switch))
        if bs is not None:
            choice_info.update(bs)
            events.append({"type": "choice", "choice": choice_info})
            choice_info = None
        if line.startswith(prefix_read_chunk_update):
            events.append({"type": "update", "update": parse_update(extract_json(line, prefix_read_chunk))})
        if line.startswith(prefix_read_chunk_end):
            end = parse_end(extract_json(line, prefix_read_chunk))
            return {"agents": agents_info, "events": events, "end": end}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()
    with compress_open(args.src, "rt") as rf:
        with compress_open(args.dst, "wt") as wf:
            while True:
                parsed = parse_one_battle(rf)
                if parsed is None:
                    break
                wf.write(json.dumps(parsed) + "\n")


if __name__ == '__main__':
    main()
