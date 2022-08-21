from typing import List, NamedTuple, Optional
import json
import re
import uuid
from logging import getLogger

from pokeai.sim.sim_proxy import SimProxy, sim_proxy
from pokeai.sim.party_generator import Party
from pokeai.sim.simutil import sim_util
from pokeai.util import side2idx

logger = getLogger(__name__)

def make_battle_id() -> str:
    return uuid.uuid4()

class SimBattleEvent(NamedTuple):
    type: str

# SimBattleEventUpdate(SimBattleEvent) と書きたいのだがエラーが生じる
class SimBattleEventUpdate(NamedTuple):
    msg: str
    args: List[str]
    type: str = 'update'

class SimBattleEventRequest(NamedTuple):
    action_type: str
    request: dict
    type: str = 'request'

class SimObservation(NamedTuple):
    battle_events: List[SimBattleEvent]
    is_end: bool = False
    winner: Optional[str] = None

class SideContext:
    side: str
    side_party: Party
    last_request: dict  # 最新の行動選択時における味方の状態
    last_request_my_action: str  # 直前のrequestで要求された行動の種類 none | turn_start | force_switch
    battle_events: List[SimBattleEvent]

    def __init__(self, side: str, side_party: Party) -> None:
        self.side = side
        self.side_party = side_party
        self.battle_events = []
    
    def _handle_request(self, msgargs: List[str]) -> None:
        """
        |request|{"active":[{"moves":[{"move":"Toxic", ...
        """
        # 味方の状態(技、残りPP, 控えのポケモンのHPなど)
        request = json.loads(msgargs[0])
        self.last_request = request

        if request.get('wait'):
            # 相手だけが強制交換の状況
            # 選択肢なし、返答自体なし
            self.last_request_my_action = 'none'
        elif request.get('forceSwitch'):
            # 強制交換(瀕死)
            # このタイミングで交換先を選ぶ
            # 厳密には、この後にターンの経過（どの技が使われたかなど）のメッセージが来るのでそれも判断に取り入れるべきだが、現状では無視
            self.last_request_my_action = 'force_switch'
        elif request.get('active'):
            # 通常のターン開始時の行動選択
            # この後に前回ターンの経過が来るので、それを待った上でAIが判断する
            self.last_request_my_action = 'turn_start'
        else:
            # バトル前の見せ合いで生じるようだが未対応
            raise ValueError("Unknown situation of choice")

    def process_chunk(self, chunk_type: str, data: str) -> Optional[SimObservation]:
        obs = None
        for line in data.splitlines():
            # |request|xxx
            lineparts = line.split('|')
            msg = lineparts[1]
            msgargs = lineparts[2:]
            if msg == 'request':
                self._handle_request(msgargs)
            else:
                self.battle_events.append(SimBattleEventUpdate(msg=msg, args=msgargs))
        if chunk_type == "update":
            if self.last_request_my_action == 'turn_start':
                # TODO ターン開始時の行動要求されている
                self.battle_events.append(SimBattleEventRequest(action_type=self.last_request_my_action, request=self.last_request))
            elif self.last_request_my_action == 'force_switch':
                # TODO 強制交代の行動要求されている
                self.battle_events.append(SimBattleEventRequest(action_type=self.last_request_my_action, request=self.last_request))
            else:
                # TODO 相手だけ行動要求されているが、同時に行動決定をしないといけないのでどの選択肢を選んでも同じとなる観測を返す
                self.battle_events.append(SimBattleEventRequest(action_type=self.last_request_my_action, request=self.last_request))
            self.last_request_my_action = 'none'
            obs = SimObservation(battle_events=self.battle_events, is_end=False)
        return obs
    
    def process_end(self, winner: str) -> SimObservation:
        """
        バトル終了情報を付加して観測を返す
        """
        return SimObservation(battle_events=self.battle_events, is_end=True, winner=winner)

class Sim:
    MAX_TURNS: int = 100
    battle_id: str
    _proxy: SimProxy
    _side_contexts: List[SideContext]
    def __init__(self) -> None:
        self._proxy = sim_proxy
        self._proxy_simid = self._proxy.open()
        self.battle_id = make_battle_id()

    def _makePartySpec(self, name, party):
        return {'name': name, 'team': sim_util.call('packTeam', {'party': party})}

    def _write_chunk(self, commands: List[str]):
        logger.debug("writeChunk " + json.dumps('\n'.join(commands)))
        self._proxy.write(self._proxy_simid, '\n'.join(commands))

    def start(self, parties: List[Party]) -> List[SimObservation]:
        spec = {'formatid': 'gen2customgame'}
        self._write_chunk([
            f'>start {json.dumps(spec)}',
            f'>player p1 {json.dumps(self._makePartySpec("p1", parties[0]))}',
            f'>player p2 {json.dumps(self._makePartySpec("p2", parties[1]))}',
        ])
        self._side_contexts = [SideContext('p1', parties[0]), SideContext('p2', parties[1])]
        return self._proceed_until_request()

    def step(self, actions: List[Optional[str]]) -> List[SimObservation]:
        # 両プレイヤーの行動を選択し、次の行動選択が必要となるタイミングまでシミュレータを進める。
        for i, side in enumerate(['p1', 'p2']):
            if actions[i] is not None:
                self._write_chunk([f'>{side} {actions[i]}'])
        return self._proceed_until_request()

    def _proceed_until_request(self) -> List[SimObservation]:
        sent_forcetie = False
        while True:
            chunk_type, chunk_data = self._proxy.read(self._proxy_simid).split('\n', 1)
            if chunk_data.find(f'|turn|{Sim.MAX_TURNS}') >= 0 and not sent_forcetie:
                # 長すぎるバトルをカット
                logger.warning(f"battle reached to MAX_TURNS turns, exiting as tie")
                self._write_chunk([
                    f'>forcetie'
                ])
                sent_forcetie = True
                # この後はendメッセージを待つだけ。エージェントにchoiceを送らせてはいけない
                # (|error|[Invalid choice] Can't do anything: The game is over)というエラーになる
                continue
            try:
                obses = self._process_chunk(chunk_type, chunk_data, sent_forcetie)
                if obses is not None:
                    return obses
            except Exception as ex:
                raise ValueError(f"Exception on processing chunk {chunk_type},{chunk_data}", ex)

    def _extract_update_for_side(self, side: str, chunk_data: str):
        # Pokemon-Showdown/sim/battle.ts の移植
        if side == 'omniscient':
            # 全データ取得
            return re.sub('\n\\|split\\|p[1234]\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
        # 各プレイヤーごとの秘密情報を、他のプレイヤー向けには削除する
        # '|split|p1'の次の行は、p1にのみ送る（他のプレイヤーの場合削除）
        if side.startswith('p'):
            chunk_data = re.sub('\n\\|split\\|' + side + '\n([^\n]*)\n(?:[^\n]*)', '\n\\1', chunk_data)
        return re.sub('\n\\|split\\|(?:[^\n]*)\n(?:[^\n]*)\n\n?', '\n', chunk_data)  # 対象でない秘密データ削除

    def _process_chunk(self, chunk_type: str, chunk_data: str, sent_forcetie: bool) -> Optional[List[SimObservation]]:
        """
        chunkを処理する。
        :param chunk_type:
        :param chunk_data:
        :return:
        """
        # 振り分けについては
        # battle-stream.ts を参考にする
        if chunk_type == 'end':
            # バトル終了
            obs_list = []
            battle_result = json.loads(chunk_data)
            winner = battle_result['winner']  # 'p1', 'p2', '' (forcetieで引き分けの時)
            for side in ['p1', 'p2']:
                obs = self._side_contexts[side2idx(side)].process_end(winner)
                assert obs is not None
                obs_list.append(obs)
            return obs_list
        if sent_forcetie:
            # forcetieを送った後は、endメッセージ以外無視
            return None
        if chunk_type == 'sideupdate':
            side, side_data = chunk_data.split('\n')
            self._side_contexts[side2idx(side)].process_chunk(chunk_type, side_data)
        elif chunk_type == 'update':
            obs_list = []
            for side in ['p1', 'p2']:
                side_data = self._extract_update_for_side(side, chunk_data)
                obs = self._side_contexts[side2idx(side)].process_chunk(chunk_type, side_data)
                assert obs is not None
                obs_list.append(obs)
            return obs_list
        else:
            raise NotImplementedError(f"Unknown chunk type {chunk_type}")
