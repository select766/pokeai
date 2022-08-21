"""
シミュレータラッパー
"""
import os
import random
import subprocess
import json
import re
from typing import List, Optional
from logging import getLogger

from pokeai.ai.action_policy import ActionPolicy
from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.party_generator import Party
from pokeai.sim.simutil import sim_util
from pokeai.util import ROOT_DIR, side2idx, idx2side

logger = getLogger(__name__)


class SimV1:
    """
    シミュレータ
    """
    parties: List[Party]
    processors: List[BattleStreamProcessor]
    policies: List[ActionPolicy]
    proc: subprocess.Popen
    n_battle: int

    def __init__(self):
        self.n_battle = 0
        self.proc = None
        self.parties = None
        self.processors = None

    def set_party(self, parites: List[Party]):
        self.parties = parites

    def set_processor(self, processors: List[BattleStreamProcessor]):
        self.processors = processors

    def _writeChunk(self, commands: List[str]):
        logger.debug("writeChunk " + json.dumps('\n'.join(commands)))
        self.proc.stdin.write(json.dumps('\n'.join(commands)) + '\n')
        self.proc.stdin.flush()

    def _readChunk(self) -> List[str]:
        line = self.proc.stdout.readline()
        logger.debug("readChunk " + line)
        rawstr = json.loads(line)
        return rawstr.split('\n', 1)  # 最初の1要素(update, endなど)のみ分離

    def run(self):
        """
        バトルを１回行う
        :return: endメッセージの内容 {'winner': 'p1', 'turns': 34, ...}
        """
        # シミュレータプログラムの実行。長く運用するとクラッシュすることがあるので定期的に再起動
        if self.n_battle >= 1000:
            self.proc.stdin.close()
            self.proc.terminate()
            self.proc = None
            self.n_battle = 0
        if self.proc is None:
            self.proc = subprocess.Popen(['node', 'js/simpipe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         encoding='utf-8', cwd=str(ROOT_DIR))
        self.n_battle += 1

        for i in [0, 1]:
            self.processors[i].start_battle(idx2side(i), self.parties[i])

        self._writeStart()
        sent_forcetie = False
        while True:
            chunk_type, chunk_data = self._readChunk()
            battle_result = None
            if chunk_data.find('|turn|100') >= 0 and not sent_forcetie:
                # 長すぎるバトルをカット
                logger.warning(f"battle reached to 100 turns, exiting as tie")
                self._writeChunk([
                    f'>forcetie'
                ])
                sent_forcetie = True
                # この後はendメッセージを待つだけ。エージェントにchoiceを送らせてはいけない
                # (|error|[Invalid choice] Can't do anything: The game is over)というエラーになる
                continue
            try:
                battle_result = self._processChunk(chunk_type, chunk_data, sent_forcetie)
            except Exception as ex:
                raise ValueError(f"Exception on processing chunk {chunk_type},{chunk_data}", ex)
            if battle_result is not None:
                # FIXME: ここで呼ぶべきか、processorにメソッドを設けるべきか
                winner = battle_result['winner']  # 'p1', 'p2', '' (forcetieで引き分けの時)
                reward_p1 = {'p1': 1.0, 'p2': -1.0, '': 0.0}[winner]
                for side, sign in [('p1', 1.0), ('p2', -1.0)]:
                    self.processors[side2idx(side)].policy.game_end(reward=reward_p1 * sign)

                return battle_result

    def _extractUpdateForSide(self, side: str, chunk_data: str):
        # Pokemon-Showdown/sim/battle.ts の移植
        if side == 'omniscient':
            # 全データ取得
            return re.sub('\n\\|split\\|p[1234]\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
        # 各プレイヤーごとの秘密情報を、他のプレイヤー向けには削除する
        # '|split|p1'の次の行は、p1にのみ送る（他のプレイヤーの場合削除）
        if side.startswith('p'):
            chunk_data = re.sub('\n\\|split\\|' + side + '\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
        return re.sub('\n\\|split\\|(?:[^\n]*)\n(?:[^\n]*)\n\n?', '\n', chunk_data)  # 対象でない秘密データ削除

    def _processChunk(self, chunk_type: str, chunk_data: str, sent_forcetie: bool) -> Optional[object]:
        """
        chunkの種類ごとに適切なプロセッサに振り分ける。バトル終了の場合はendメッセージの内容を返す
        :param chunk_type:
        :param chunk_data:
        :return:
        """
        # 振り分けについては
        # battle-stream.ts を参考にする
        if chunk_type == 'end':
            # バトル終了
            return json.loads(chunk_data)  # バトルの結果を返す
        if sent_forcetie:
            # forcetieを送った後は、endメッセージ以外無視
            return None
        if chunk_type == 'sideupdate':
            side, side_data = chunk_data.split('\n')
            choice = self.processors[side2idx(side)].process_chunk(chunk_type, side_data)
            if choice is not None:
                self._writeChunk([f'>{side} {choice}'])
        elif chunk_type == 'update':
            for side in ['p1', 'p2']:
                choice = self.processors[side2idx(side)].process_chunk(chunk_type,
                                                                       self._extractUpdateForSide(side, chunk_data))
                if choice is not None:
                    self._writeChunk([f'>{side} {choice}'])
        else:
            raise NotImplementedError(f"Unknown chunk type {chunk_type}")

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
