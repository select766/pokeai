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

from pokeai.sim.battle_stream_processor import BattleStreamProcessor
from pokeai.sim.party_generator import Party
from pokeai.sim.simutil import sim_util
from pokeai.util import ROOT_DIR, side2idx, idx2side

logger = getLogger(__name__)


class Sim:
    """
    シミュレータ
    """
    parties: List[Party]
    processors: List[BattleStreamProcessor]

    def __init__(self):
        self.proc = subprocess.Popen(['node', 'js/simpipe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     encoding='utf-8', cwd=str(ROOT_DIR))
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
        for i in [0, 1]:
            self.processors[i].start_battle(idx2side(i))

        self._writeStart()
        while True:
            chunk_type, chunk_data = self._readChunk()
            battle_result = None
            try:
                battle_result = self._processChunk(chunk_type, chunk_data)
            except Exception as ex:
                raise ValueError(f"Exception on processing chunk {chunk_type},{chunk_data}", ex)
            if battle_result is not None:
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

    def _processChunk(self, chunk_type: str, chunk_data: str) -> Optional[object]:
        """
        chunkの種類ごとに適切なプロセッサに振り分ける。バトル終了の場合はendメッセージの内容を返す
        :param chunk_type:
        :param chunk_data:
        :return:
        """
        # 振り分けについては
        # battle-stream.ts を参考にする
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
        elif chunk_type == 'end':
            # バトル終了
            return json.loads(chunk_data)  # バトルの結果を返す
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
