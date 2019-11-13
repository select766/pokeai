"""
シミュレータラッパー
"""
import os
import random
import subprocess
import json
from typing import List, Optional
from logging import getLogger

from pokeai.sim.party_generator import Party
from pokeai.sim.simutil import sim_util
from pokeai.util import ROOT_DIR

logger = getLogger(__name__)


class Sim:
    """
    シミュレータ
    """
    parties: List[Party]

    def __init__(self):
        self.proc = subprocess.Popen(['node', 'js/simpipe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     encoding='utf-8', cwd=str(ROOT_DIR))
        self.parties = None

    def set_party(self, parites: List[Party]):
        self.parties = parites

    def _writeChunk(self, commands: List[str]):
        logger.debug("writeChunk " + json.dumps('\n'.join(commands)))
        self.proc.stdin.write(json.dumps('\n'.join(commands)) + '\n')
        self.proc.stdin.flush()

    def _readChunk(self) -> List[str]:
        line = self.proc.stdout.readline()
        logger.debug("readChunk " + line)
        rawstr = json.loads(line)
        return rawstr.split('\n')

    def run(self):
        """
        バトルを１回行う
        :return: endメッセージの内容 {'winner': 'p1', 'turns': 34, ...}
        """
        self._writeStart()
        c = None
        while True:
            c = self._readChunk()
            battle_result = None
            try:
                battle_result = self._processChunk(c)
            except Exception as ex:
                raise ValueError(f"Exception on processing chunk {c}", ex)
            if battle_result is not None:
                return battle_result

    def _processChunk(self, chunk: List[str]) -> Optional[object]:
        if chunk[0] == 'sideupdate':
            self._processSideUpdate(chunk)
        elif chunk[0] == 'update':
            # TODO: 状態の解釈
            pass
        elif chunk[0] == 'end':
            # バトル終了
            return json.loads(chunk[1])  # バトルの結果を返す
        else:
            raise NotImplementedError(f"Unknown chunk key {chunk[0]}")

    def _processSideUpdate(self, chunk: List[str]):
        sideplayer = chunk[1]  # p1 or p2
        assert len(chunk) == 3
        msg = chunk[2]  # |request|{"active":[{"moves":...
        if msg.startswith('|request|'):
            request = json.loads(msg[len('|request|'):])
            choice = self._randomChoice(request)
            if choice:
                self._writeChunk([f'>{sideplayer} {choice}'])

    def _randomChoice(self, request) -> Optional[str]:
        # Pokemon-Showdown/sim/tools/random-player-ai.ts
        # を参考にシングルバトル特化で選択肢を選択
        if request.get('wait'):
            # 相手だけが強制交換の状況
            # 選択肢なし、返答自体なし
            return None
        elif forceSwitch := request.get('forceSwitch'):
            # 強制交換(瀕死)
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
            assert len(active) == 1  # シングルバトル
            move_choices = []
            trapped = False
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
        else:
            # バトル前の見せ合いで生じるようだが未対応
            raise ValueError("Unknown situation of choice")

    def _makePartySpec(self, name, party):
        return {'name': name, 'team': sim_util.call('packTeam', {'party': party})}

    def _writeStart(self):
        if self.parties is None:
            raise Exception('parties not set')
        spec = {'formatid': 'gen2customgame'}
        self._writeChunk([
            f'>start {json.dumps(spec)}',
            f'>player p1 {json.dumps(self._makePartySpec("p1", self.parties[0]))}',
            f'>player p2 {json.dumps(self._makePartySpec("p2", self.parties[1]))}',
        ])
