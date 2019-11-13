import subprocess
import json
from pokeai.util import ROOT_DIR


class SimUtilError(Exception):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj


class SimUtil:
    """
    シミュレータの付属機能呼び出し
    """

    def __init__(self):
        self.proc = subprocess.Popen(['node', 'js/simutil'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     encoding='utf-8', cwd=str(ROOT_DIR))

    def call(self, method: str, params):
        self.proc.stdin.write(json.dumps({'method': method, 'params': params}) + '\n')
        self.proc.stdin.flush()
        result = json.loads(self.proc.stdout.readline())
        if result['error'] is not None:
            raise SimUtilError(result['error'])
        return result['result']


sim_util = SimUtil()
