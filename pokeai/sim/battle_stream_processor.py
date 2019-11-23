"""
シミュレータからのメッセージを解釈し、AIを制御する
"""
import json
import random
import re
from typing import Optional, List, Tuple
from logging import getLogger

from pokeai.ai.battle_status import BattleStatus, parse_hp_condition

logger = getLogger(__name__)


class BattleStreamProcessor:
    side: Optional[str]  # p1 or p2
    last_request: dict  # 最新の行動選択時における味方の状態
    battle_status: BattleStatus
    policy: "ActionPolicy"
    # 処理しないメッセージ（進行上重要でなく、AIの判断に使わない情報）
    ignore_msgs = ['',
                   'debug',
                   'player',
                   'gametype',
                   'gen',
                   'tier',
                   'rule',
                   'start',
                   'move',  # 使われた技
                   'upkeep',
                   '-activate',  # 何らかの効果が発生(身代わりで技が防がれた時など)
                   '-supereffective',  # こうかはばつぐんだ
                   '-resisted',  # こうかはいまひとつのようだ
                   '-immune',  # こうかはないようだ
                   '-crit',  # きゅうしょにあたった
                   '-miss',  # 攻撃失敗
                   '-fail',  # 攻撃失敗
                   '-prepare',  # 攻撃の「溜め」
                   '-mustrecharge',  # 次のターン動けない（はかいこうせんを撃った直後などに発生）
                   '-nothing',  # はねるなど無意味
                   '-fieldactivate',  # 場のポケモン全員に効果が発生(ほろびのうた)
                   '-singleturn',  # そのターンのみの状態変化(こらえるなど)
                   '-singlemove',  # その技を使っている間のみの状態変化（いかりなど）
                   '-hint',  # 追加説明、|-hint|In Gen 2, draining moves always miss against Substitute.
                   '-anim',  # アニメーション？
                   '-hitcount',  # *かいあたった
                   '-ohko',  # いちげきひっさつ
                   # |move|p1a: Xatu|Solar Beam||[still]
                   # |-prepare|p1a: Xatu|Solar Beam|p2a: Skiploom
                   # |-anim|p1a: Xatu|Solar Beam|p2a: Skiploom
                   # |-resisted|p2a: Skiploom
                   # |-damage|p2a: Skiploom|163/176
                   'cant',  # 麻痺などで行動ができない
                   'win',  # 勝敗決定(勝者の取得は別途endメッセージで行う)
                   ]

    def __init__(self):
        self.side = None
        self.policy = None
        self._handlers = {
            'request': self._handle_request,
            'switch': self._handle_switch,
            'drag': self._handle_drag,
            'teamsize': self._handle_teamsize,
            'turn': self._handle_turn,
            '-damage': self._handle_damage,
            '-heal': self._handle_heal,
            '-start': self._handle_start,
            '-end': self._handle_end,
            '-status': self._handle_status,
            '-curestatus': self._handle_curestatus,
            '-sethp': self._handle_sethp,
            '-boost': self._handle_boost,
            '-unboost': self._handle_unboost,
            '-setboost': self._handle_setboost,
            '-copyboost': self._handle_copyboost,
            '-clearallboost': self._handle_clearallboost,
            '-sidestart': self._handle_sidestart,
            '-sideend': self._handle_sideend,
            'faint': self._handle_faint,
            '-weather': self._handle_weather,
        }

    def set_policy(self, policy: "ActionPolicy"):
        self.policy = policy

    def start_battle(self, side: str):
        """
        バトルの開始。バトルの状態を初期化する。
        :param side:
        :return:
        """
        assert self.policy is not None
        self.side = side
        self.last_request = None
        # FIXME: BattleStatusと責任境界が分かれてない
        self.battle_status = BattleStatus(side)

    def process_chunk(self, chunk_type: str, data: str) -> Optional[str]:
        """
        chunkを処理し、行動がある場合はそれを返す
        :param chunk_type:
        :param data:
        :return: "move 2"や"switch 1"のような行動
        """
        choice = None
        for line in data.splitlines():
            # |request|xxx
            lineparts = line.split('|')
            msg = lineparts[1]
            msgargs = lineparts[2:]
            msgchoice = None
            handler = self._handlers.get(msg)
            if handler is not None:
                msgchoice = handler(msgargs)
            elif msg in BattleStreamProcessor.ignore_msgs:
                # 安全に無視できるメッセージ
                pass
            else:
                raise NotImplementedError(f"unknown message {msg} in {data}")
            if msgchoice is not None:
                assert choice is None, "multiple choice occurred for one chunk"
                choice = msgchoice
        return choice

    def _handle_request(self, msgargs: List[str]) -> Optional[str]:
        """
        |request|{"active":[{"moves":[{"move":"Toxic", ...
        :param data:
        :return: 行動選択を行う場合は返す
        """
        # 味方の状態(技、残りPP, 控えのポケモンのHPなど)
        request = json.loads(msgargs[0])
        self.last_request = request

        if request.get('wait'):
            # 相手だけが強制交換の状況
            # 選択肢なし、返答自体なし
            return None
        elif request.get('forceSwitch'):
            # 強制交換(瀕死)
            # このタイミングで交換先を選ぶ
            # 厳密には、この後にターンの経過（どの技が使われたかなど）のメッセージが来るのでそれも判断に取り入れるべきだが、現状では無視
            return self.policy.choice_force_switch(self.battle_status, request)
        elif request.get('active'):
            # 通常のターン開始時の行動選択
            # この後に前回ターンの経過が来るので、それを待った上でAIが判断する
            pass
        else:
            # バトル前の見せ合いで生じるようだが未対応
            raise ValueError("Unknown situation of choice")
        return None

    def _handle_switch(self, msgargs: List[str]) -> Optional[str]:
        """
        |switch|p1a: Ninetales|Ninetales, L50, M|179/179
        :return:
        """
        self.battle_status.switch(msgargs[0], msgargs[1], msgargs[2])
        return None

    def _handle_drag(self, msgargs: List[str]) -> Optional[str]:
        """
        switchと似ているが強制的に引き摺り出された場合（吠える）
        |move|p2a: Moltres|Roar|p1a: Ninetales
        |drag|p1a: Natu|Natu, L55, M|116/160
        :return:
        """
        self.battle_status.switch(msgargs[0], msgargs[1], msgargs[2])
        # 今のところswitchと違いはない
        return None

    def _handle_teamsize(self, msgargs: List[str]) -> Optional[str]:
        """
        |teamsize|p2|3
        :return:
        """
        teamsize = int(msgargs[1])
        ss = self.battle_status.side_statuses[msgargs[0]]
        ss.total_pokes = teamsize
        ss.remaining_pokes = teamsize
        return None

    def _handle_turn(self, msgargs: List[str]) -> Optional[str]:
        """
        |turn|1
        :return:
        """
        # 最初のターンは1
        turn = int(msgargs[0])
        self.battle_status.turn = turn
        logger.debug('turn_start ' + self.battle_status.json_dumps())
        return self.policy.choice_turn_start(self.battle_status, self.last_request)

    def _handle_start(self, msgargs: List[str]) -> Optional[str]:
        """
        状態変化開始
        :param msgargs:
        :return:
        """
        # |-start|p1a: Ninetales|Substitute
        self.battle_status.get_side(msgargs[0]).active.volatile_statuses.add(msgargs[1])
        return None

    def _handle_end(self, msgargs: List[str]) -> Optional[str]:
        # 状態変化終了
        # |-start|p1a: Ninetales|Substitute
        # set.removeでなくset.discard(要素なくてもエラーにならない)を使用
        # |-end|p2a: Dodrio|move: Bide
        # という例あり
        self.battle_status.get_side(msgargs[0]).active.volatile_statuses.discard(msgargs[1])
        return None

    def _handle_damage(self, msgargs: List[str]) -> Optional[str]:
        # ダメージを受けた
        # |-damage|p1a: Ninetales|135/179
        # |-damage|p2a: Granbull|184/196 tox|[from] psn
        hp_current, hp_max, status = parse_hp_condition(msgargs[1])
        active = self.battle_status.get_side(msgargs[0]).active
        active.hp_current = hp_current
        active.status = status
        return None

    def _handle_heal(self, msgargs: List[str]) -> Optional[str]:
        # 回復
        # |move|p2a: Skiploom|Giga Drain|p1a: Natu
        # |-resisted|p1a: Natu
        # |-damage|p1a: Natu|139/160
        # |-heal|p2a: Skiploom|132/176|[from] drain|[of] p1a: Natu
        hp_current, hp_max, status = parse_hp_condition(msgargs[1])
        active = self.battle_status.get_side(msgargs[0]).active
        active.hp_current = hp_current
        active.status = status
        return None

    def _handle_status(self, msgargs: List[str]) -> Optional[str]:
        # 状態異常が発生
        # |move|p1a: Ninetales|Toxic|p2a: Granbull
        # |-status|p2a: Granbull|tox
        self.battle_status.get_side(msgargs[0]).active.status = msgargs[1]
        return None

    def _handle_curestatus(self, msgargs: List[str]) -> Optional[str]:
        # 状態異常が回復
        # |-curestatus|p2a: Granbull|tox
        self.battle_status.get_side(msgargs[0]).active.status = ''
        return None

    def _handle_sethp(self, msgargs: List[str]) -> Optional[str]:
        # HPを特定の値にセット(いたみわけで発生)
        # |-sethp|p1a: Cleffa|104/171 par|[from] move: Pain Split|[silent]
        hp_current, hp_max, status = parse_hp_condition(msgargs[1])
        active = self.battle_status.get_side(msgargs[0]).active
        active.hp_current = hp_current
        active.status = status
        return None

    def _handle_boost(self, msgargs: List[str]) -> Optional[str]:
        # ランク変化（上がる）
        # |move|p2a: Porygon|Barrier|p2a: Porygon
        # |-boost|p2a: Porygon|def|2
        # 数値は変化量
        self.battle_status.get_side(msgargs[0]).active.rank_boost(msgargs[1], int(msgargs[2]))
        return None

    def _handle_unboost(self, msgargs: List[str]) -> Optional[str]:
        # ランク変化（下がる）
        # |move|p2a: Granbull|Tail Whip|p1a: Ninetales
        # |-unboost|p1a: Ninetales|def|1
        self.battle_status.get_side(msgargs[0]).active.rank_unboost(msgargs[1], int(msgargs[2]))
        return None

    def _handle_setboost(self, msgargs: List[str]) -> Optional[str]:
        # ランク変化（特定の値をセット）　はらだいこなど
        # 数値は変化後の値
        self.battle_status.get_side(msgargs[0]).active.rank_setboost(msgargs[1], int(msgargs[2]))
        return None

    def _handle_copyboost(self, msgargs: List[str]) -> Optional[str]:
        # ランク変化（相手のものをそのままコピー）
        # |move|p1a: Natu|Psych Up|p2a: Granbull
        # |-copyboost|p1a: Natu|p2a: Granbull|[from] move: Psych Up
        # SIM-PROTOCOL.mdだと
        # |-copyboost|SOURCE|TARGET
        # という説明になっているが、実際のメッセージは逆のように見える
        # じこあんじをしたのはNatuなのでNatuが変化する側
        source = self.battle_status.get_side(msgargs[1]).active
        target = self.battle_status.get_side(msgargs[0]).active
        target.ranks = source.ranks.copy()
        return None

    def _handle_clearallboost(self, msgargs: List[str]) -> Optional[str]:
        # 全てのポケモンの全てのランク変化をリセット（くろいきり）
        # |move|p2a: Golbat|Haze|p2a: Golbat
        # |-clearallboost
        for side in self.battle_status.side_statuses.values():
            side.active.rank_clearallboost()
        return None

    def _handle_sidestart(self, msgargs: List[str]) -> Optional[str]:
        # プレイヤーの場に生じる状態の発生
        # |move|p2a: Skiploom|Reflect|p2a: Skiploom
        # |-sidestart|p2: p2|Reflect
        self.battle_status.get_side(msgargs[0]).side_statuses.add(msgargs[1])
        return None

    def _handle_sideend(self, msgargs: List[str]) -> Optional[str]:
        # プレイヤーの場に生じる状態の消滅
        # |-sideend|p2: p2|Safeguard
        self.battle_status.get_side(msgargs[0]).side_statuses.remove(msgargs[1])
        return None

    def _handle_faint(self, msgargs: List[str]) -> Optional[str]:
        # ポケモンの瀕死
        # |-damage|p2a: Granbull|0 fnt|[from] psn|[of] p1a: Ninetales
        # |faint|p2a: Granbull
        self.battle_status.get_side(msgargs[0]).remaining_pokes -= 1
        return None

    def _handle_weather(self, msgargs: List[str]) -> Optional[str]:
        # 天候の開始/終了 (天候のところにnone)
        # |move|p1a: Xatu|Sunny Day|p1a: Xatu
        # |-weather|SunnyDay
        # SunnyDay,RainDance,Sandstorm,none
        self.battle_status.weather = msgargs[0]
        return None


"""
ほろびのうたの挙動

発動ターン
|switch|p1a: Teddiursa|Teddiursa, L55, M|182/182
|move|p2a: Marowak|Perish Song|p2a: Marowak
|-start|p1a: Teddiursa|perish3|[silent]
|-start|p2a: Marowak|perish3|[silent]
|-fieldactivate|move: Perish Song
|
|-start|p2a: Marowak|perish3
|-start|p1a: Teddiursa|perish3
|upkeep
|turn|14

その後、perish2, perish1, perish0がターン終了ごとに開始
（perishXが発動した時にperish(X+1)状態はendされない模様）
perish0が発生した直後に瀕死となる
"""
