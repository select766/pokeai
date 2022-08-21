# シミュレータとの通信を行うモジュール
# シミュレータは比較的遅い（1ターン1ms程度）ため、複数プロセス分のシミュレータを束ねる

from collections import defaultdict
from typing import ClassVar, Dict, List
import json
import subprocess
from pokeai.util import ROOT_DIR

class SimProxy:
    max_processes: int # 最大プロセス数
    _processes: Dict[int, subprocess.Popen]
    _idmap: Dict[int, int] # simulator id, process id
    _proccount: Dict[int, int] # process id, number of simulators
    _next_process_id: int
    _next_simulator_id: int
    _pending_read_item: Dict[int, List[str]] # simulator id, pending read items

    def __init__(self, max_processes=0) -> None:
        if max_processes <= 0:
            import multiprocessing
            max_processes = multiprocessing.cpu_count()
        self.max_processes = max_processes
        self._processes = {}
        self._idmap = {}
        self._proccount = {}
        self._next_process_id = 0
        self._next_simulator_id = 0
        self._pending_read_item = defaultdict(list)
    
    def _launch(self):
        return subprocess.Popen(['node', 'js/simpipemulti'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                encoding='utf-8', cwd=str(ROOT_DIR))

    def _writejson(self, pid: int, obj: object) -> None:
        proc = self._processes[pid]
        proc.stdin.write(json.dumps(obj) + '\n')
        proc.stdin.flush()

    def open(self) -> int:
        # プロセス数がmax_processesより少ないならプロセスを新たに立てる
        if len(self._processes) < self.max_processes:
            proc = self._launch()
            pid = self._next_process_id
            self._next_process_id += 1
            self._processes[pid] = proc
            self._proccount[pid] = 0
        else:
            # 既存プロセスで一番シミュレータ数が少ないプロセスを選んでシミュレータを立てる
            proccount = [(cnt, pid) for pid, cnt in self._proccount.items()]
            proccount.sort()
            pid = proccount[0][1]
        simid = self._next_simulator_id
        self._next_simulator_id += 1
        self._proccount[pid] += 1
        self._idmap[simid] = pid
        self._writejson(pid, {'type': 'open', 'id': str(simid)})
        return simid

    def write(self, simid: int, chunk: str) -> None:
        pid = self._idmap[simid]
        self._writejson(pid, {'type': 'write', 'id': str(simid), 'chunk': chunk})
    
    def read(self, simid: int) -> str:
        pend = self._pending_read_item[simid]
        if len(pend) > 0:
            return pend.pop(0)
        pid = self._idmap[simid]
        proc = self._processes[pid]
        while True:
            item = json.loads(proc.stdout.readline())
            if item['type'] != 'read':
                continue
            read_simid = int(item['id'])
            chunk = item['chunk']
            if read_simid == simid:
                return chunk
            else:
                # 読みたいシミュレータ以外のメッセージが来ていたら、将来readされた時に返すため保存する
                self._pending_read_item[read_simid].append(chunk)

    def close(self, simid: int) -> None:
        # 長時間実行でパフォーマンスが悪くなるようなら、一定回数シミュレーションしたプロセスを終了して別のプロセスを立てる
        pid = self._idmap[simid]
        self._writejson(pid, {'type': 'close', 'id': str(simid)})
        del self._idmap[simid]
        self._proccount[pid] -= 1

sim_proxy = SimProxy()
