"""
シミュレータからのメッセージを解釈し、AIを制御する
"""
import json
import random
import re
from typing import Optional, List, Tuple
from logging import getLogger

from pokeai.ai.battle_status import BattleStatus

logger = getLogger(__name__)


class BattleStreamProcessor:
    side: Optional[str]  # p1 or p2
    last_request: dict  # 最新の行動選択時における味方の状態
    battle_status: BattleStatus
    # 処理しないメッセージ（進行上重要でなく、AIの判断に使わない情報）
    ignore_msgs = ['',
                   'debug',
                   'player',
                   'teamsize',
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
        self._handlers = {
            'request': self._handle_request,
            'switch': self._handle_switch,
            'drag': self._handle_drag,
            'turn': self._handle_turn,
            '-damage': self._handle_damage,
            '-heal': self._handle_heal,
            '-start': self._handle_start,
            '-end': self._handle_end,
            '-status': self._handle_status,
            '-curestatus': self._handle_curestatus,
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

    def start_battle(self, side: str):
        """
        バトルの開始。バトルの状態を初期化する。
        :param side:
        :return:
        """
        self.side = side
        self.last_request = None
        self.battle_status = BattleStatus()

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
        elif forceSwitch := request.get('forceSwitch'):
            # 強制交換(瀕死)
            # このタイミングで交換先を選ぶ
            # 厳密には、この後にターンの経過（どの技が使われたかなど）のメッセージが来るのでそれも判断に取り入れるべきだが、現状では無視
            # TODO: ランダムではなくAIに移譲するようにする
            # TODO: バトンタッチ対応
            assert len(forceSwitch) == 1  # シングルバトル
            assert forceSwitch[0]
            switch_choices = []
            for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
                if backpokemon['active']:
                    # 場に出ている
                    continue
                if backpokemon['condition'].endswith(' fnt'):
                    # 瀕死状態
                    continue
                switch_choices.append(f"switch {i + 1}")  # 1-origin index
            assert len(switch_choices) > 0
            return random.choice(switch_choices)
        elif active := request.get('active'):
            # 通常のターン開始時の行動選択
            # この後に前回ターンの経過が来るので、それを待った上でAIが判断する
            pass
        else:
            # バトル前の見せ合いで生じるようだが未対応
            raise ValueError("Unknown situation of choice")
        return None

    def _parse_hp_condition(self, hp_condition: str) -> Tuple[int, int, str]:
        """
        HPと状態異常を表す文字列のパース
        :param hp_condition: '50/200' (現在HP=50, 最大HP=200, 状態異常なし) or '50/200 psn' (状態異常の時)
        :return: 現在HP, 最大HP, 状態異常('', 'fnt'(瀕死))
        """
        if hp_condition == '0 fnt':
            # 瀕死の時は0という表示になっている
            # 便宜上最大HP100として返している
            return 0, 100, 'fnt'
        m = re.match('^(\\d+)/(\\d+)(?: (psn|tox|par|brn|slp|frz|fnt)|)?$', hp_condition)
        # m[3]は状態異常がないときNoneとなる
        return m[1], m[2], m[3] or ''

    def _handle_switch(self, msgargs: List[str]) -> Optional[str]:
        # TODO
        """
        |switch|p1a: Ninetales|Ninetales, L50, M|179/179
        :return:
        """
        logger.info(f"switch: {msgargs}")
        return None

    def _handle_drag(self, msgargs: List[str]) -> Optional[str]:
        # TODO:
        """
        switchと似ているが強制的に引き摺り出された場合（吠える）
        |move|p2a: Moltres|Roar|p1a: Ninetales
        |drag|p1a: Natu|Natu, L55, M|116/160
        :return:
        """
        logger.info(f"drag: {msgargs}")
        return None

    def _handle_turn(self, msgargs: List[str]) -> Optional[str]:
        """
        |turn|1
        :return:
        """
        # TODO: ターン開始に従い行動選択するAIを呼び出す
        # 最初のターンは1
        turn = int(msgargs[0])
        self.battle_status.turn = turn
        return self._random_choice_turn_start()

    def _handle_start(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 状態変化開始
        # |-start|p1a: Ninetales|Substitute
        return None

    def _handle_end(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 状態変化終了
        # |-start|p1a: Ninetales|Substitute
        return None

    def _handle_damage(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ダメージを受けた
        # |-damage|p1a: Ninetales|135/179
        # |-damage|p2a: Granbull|184/196 tox|[from] psn
        return None

    def _handle_heal(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 回復
        # |move|p2a: Skiploom|Giga Drain|p1a: Natu
        # |-resisted|p1a: Natu
        # |-damage|p1a: Natu|139/160
        # |-heal|p2a: Skiploom|132/176|[from] drain|[of] p1a: Natu
        return None

    def _handle_status(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 状態異常が発生
        # |move|p1a: Ninetales|Toxic|p2a: Granbull
        # |-status|p2a: Granbull|tox
        return None

    def _handle_curestatus(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 状態異常が回復
        # |-curestatus|p2a: Granbull|tox
        return None

    def _handle_boost(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ランク変化（上がる）
        # |move|p2a: Porygon|Barrier|p2a: Porygon
        # |-boost|p2a: Porygon|def|2
        # 数値は変化量
        return None

    def _handle_unboost(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ランク変化（下がる）
        # |move|p2a: Granbull|Tail Whip|p1a: Ninetales
        # |-unboost|p1a: Ninetales|def|1
        return None

    def _handle_setboost(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ランク変化（特定の値をセット）　はらだいこなど
        # 数値は変化後の値
        return None

    def _handle_copyboost(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ランク変化（相手のものをそのままコピー）
        # |move|p1a: Natu|Psych Up|p2a: Granbull
        # |-copyboost|p1a: Natu|p2a: Granbull|[from] move: Psych Up
        # SIM-PROTOCOL.mdだと
        # |-copyboost|SOURCE|TARGET
        # という説明になっているが、実際のメッセージは逆のように見える
        # じこあんじをしたのはNatuなのでNatuが変化する側
        return None

    def _handle_clearallboost(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 全てのポケモンの全てのランク変化をリセット（くろいきり）
        # |move|p2a: Golbat|Haze|p2a: Golbat
        # |-clearallboost
        return None

    def _handle_sidestart(self, msgargs: List[str]) -> Optional[str]:
        # TODO: プレイヤーの場に生じる状態の発生
        # |move|p2a: Skiploom|Reflect|p2a: Skiploom
        # |-sidestart|p2: p2|Reflect
        return None

    def _handle_sideend(self, msgargs: List[str]) -> Optional[str]:
        # TODO: プレイヤーの場に生じる状態の消滅
        # |-sideend|p2: p2|Safeguard
        return None

    def _handle_faint(self, msgargs: List[str]) -> Optional[str]:
        # TODO: ポケモンの瀕死
        # |-damage|p2a: Granbull|0 fnt|[from] psn|[of] p1a: Ninetales
        # |faint|p2a: Granbull
        return None

    def _handle_weather(self, msgargs: List[str]) -> Optional[str]:
        # TODO: 天候の開始/終了 (天候のところにnone)
        # |move|p1a: Xatu|Sunny Day|p1a: Xatu
        # |-weather|SunnyDay
        # SunnyDay,RainDance,Sandstorm,none
        return None

    def _random_choice_turn_start(self):
        # ターン開始時の行動をランダム選択
        request = self.last_request
        active = request['active']
        assert len(active) == 1  # シングルバトル
        move_choices = []
        for i, move in enumerate(active[0]['moves']):
            if not move.get('disabled'):
                move_choices.append(f'move {i + 1}')  # 1-origin index

        # ゴッドバードなど複数ターン継続する技では、
        # [{"moves":[{"move":"Sky Attack","id":"skyattack"}],"trapped":true}],
        # のようにmoveが１要素だけになり、active.trapped:trueとなる
        # moveの番号自体ずれる(固定された技を強制選択となり"move 1"を返すこととなる)ので、番号と技の対応に注意
        switch_choices = []
        if not active[0].get('trapped'):
            for i, backpokemon in enumerate(request['side']['pokemon']):  # 手持ちの全ポケモン
                if backpokemon['active']:
                    # 場に出ている
                    continue
                if backpokemon['condition'].endswith(' fnt'):
                    # 瀕死状態
                    continue
                switch_choices.append(f"switch {i + 1}")  # 1-origin index

        if len(switch_choices) > 0 and (len(move_choices) == 0 or random.random() < 0.2):
            # 交換しかできない場合か、両方できる場合で一定確率で交換を選ぶ
            return random.choice(switch_choices)
        else:
            assert len(move_choices) > 0
            return random.choice(move_choices)


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
