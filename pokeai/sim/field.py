from enum import Enum, auto
from typing import List, Optional, Callable, Dict, Tuple

from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.field_record import FieldRecord, FieldRecordReason
from pokeai.sim.game_rng import GameRNG, GameRNGRandom, GameRNGReason
from pokeai.sim.move_calculator import MoveCalculator
from pokeai.sim.party import Party
from pokeai.sim.poke import Poke


class FieldPhase(Enum):
    BEGIN = auto()
    FIRST_MOVE = auto()
    FIRST_PC = auto()
    SECOND_MOVE = auto()
    SECOND_PC = auto()
    FAINT_CHANGE = auto()
    END_TURN = auto()
    GAME_END = auto()


class Field:
    parties: List[Party]
    turn_number: int
    """
    次に実行するphaseを指す
    """
    phase: FieldPhase
    rng: GameRNG
    first_player: int  # 先攻プレイヤー
    actions_begin: Optional[List[FieldAction]]
    actions_faint_change: Optional[List[FieldAction]]
    _phase_handlers: Dict[FieldPhase, Callable[[], FieldPhase]]

    def __init__(self, parties: List[Party]):
        self.parties = parties
        self.turn_number = 1
        self.actions_begin = None
        self.actions_faint_change = None
        self._phase_handlers = {
            FieldPhase.BEGIN: self._step_begin,
            FieldPhase.FIRST_MOVE: self._step_first_move,
            FieldPhase.FIRST_PC: self._step_first_pc,
            FieldPhase.SECOND_MOVE: self._step_second_move,
            FieldPhase.SECOND_PC: self._step_second_pc,
            FieldPhase.FAINT_CHANGE: None,  # TODO
            FieldPhase.END_TURN: self._step_end_turn,
            FieldPhase.GAME_END: None,  # TODO
        }
        self.rng = GameRNGRandom()
        self.rng.field = self
        self.first_player = None
        self.phase = FieldPhase.BEGIN

    def step(self) -> FieldPhase:
        """
        次にプレイヤーが操作可能になるまで進める
        :return:
        """
        while self._step_one() not in [FieldPhase.BEGIN, FieldPhase.FAINT_CHANGE]:
            pass
        return self.phase

    def _step_one(self):
        self.phase = self._phase_handlers[self.phase]()
        return self.phase

    def _step_begin(self) -> FieldPhase:
        """
        行動選択直後に呼ばれるターン開始処理
        :return:
        """
        self.put_record_other(f"ターン {self.turn_number} 開始")
        # 先攻決め
        speeds = []
        for player in [0, 1]:
            act = self.actions_begin[player]
            speed = self.parties[player].get().eff_s()
            if act.action_type is FieldActionType.CHANGE:
                # 交代は先攻
                speed += 10000
            speeds.append(speed)

        speeds_orig = speeds.copy()
        # 同速のとき、乱数で決める
        speed_rnd = self.rng.gen(0, GameRNGReason.MOVE_ORDER, top=1)
        if speeds[0] == speeds[1]:
            speeds[0] += speed_rnd

        if speeds[0] > speeds[1]:
            self.first_player = 0
        else:
            self.first_player = 1

        self.put_record_other(f"素早さ: {speeds_orig}, 先攻: {self.first_player}")

        return FieldPhase.FIRST_MOVE

    def put_record(self, record: FieldRecord):
        print(str(record))

    def put_record_other(self, message: str):
        """
        簡易レコード出力。型を付けるのが面倒な時用。
        :param message:
        :return:
        """
        self.put_record(FieldRecord(FieldRecordReason.OTHER, None, message))

    def _step_first_move(self) -> FieldPhase:
        self._step_move_x(0)
        # ひんしなら強制的に交換フェーズに移行
        return self._get_next_phase_if_faint() or FieldPhase.FIRST_PC

    def _step_second_move(self) -> FieldPhase:
        self._step_move_x(1)
        # ひんしなら強制的に交換フェーズに移行
        return self._get_next_phase_if_faint() or FieldPhase.SECOND_PC

    def _step_first_pc(self) -> FieldPhase:
        self._step_pc_x(0)
        # ひんしなら強制的に交換フェーズに移行
        return self._get_next_phase_if_faint() or FieldPhase.SECOND_MOVE

    def _step_second_pc(self) -> FieldPhase:
        self._step_pc_x(1)
        # ひんしなら強制的に交換フェーズに移行
        return self._get_next_phase_if_faint() or FieldPhase.END_TURN

    def _step_end_turn(self) -> FieldPhase:
        self.actions_begin = None
        self.actions_faint_change = None
        self.turn_number += 1
        return FieldPhase.BEGIN

    def _step_move_x(self, order: int):
        """
        技の発動を行う
        :param order:
        :return:
        """
        assert order in [0, 1]
        attack_player = self.first_player
        if order == 1:
            attack_player = 1 - attack_player
        defend_player = 1 - attack_player
        act = self.actions_begin[attack_player]

        self.put_record_other(f"Player {attack_player} の行動")
        attack_poke, defend_poke = self._get_fighting_pokes(attack_player)
        if act.action_type is FieldActionType.MOVE:
            # 技
            calc = MoveCalculator(attack_player, attack_poke, defend_poke, self)
            calc.run(act.move_idx)
        elif act.action_type is FieldActionType.CHANGE:
            # 交代
            attack_poke.reset()  # 今のポケモンを控えに戻す
            self.parties[attack_player].fighting_idx = act.change_idx
            self.put_record_other(f"Player {attack_player} は {self.parties[attack_player].get()} を繰り出した")
        else:
            raise ValueError

    def _step_pc_x(self, order: int):
        """
        ポケモンチェック（毒のダメージ等）を行う
        :param order:
        :return:
        """
        assert order in [0, 1]
        attack_player = self.first_player
        if order == 1:
            attack_player = 1 - attack_player
        defend_player = 1 - attack_player
        attack_poke, defend_poke = self._get_fighting_pokes(attack_player)
        # TODO 実装

    def _get_fighting_pokes(self, attack_player: int = 0) -> Tuple[Poke, Poke]:
        """
        攻撃側、守備側の場に出ているポケモンを取得する。
        :param attack_player:
        :return:
        """
        defend_player = 1 - attack_player
        return self.parties[attack_player].get(), self.parties[defend_player].get()

    def _get_next_phase_if_faint(self) -> Optional[FieldPhase]:
        """
        場に出ているポケモンがひんしになっていれば、次のphaseを返す。
        そうでなければNoneを返す。
        :return:
        """
        if self._is_any_faint():
            # 片方が全員ひんしならゲーム終了
            if self._is_any_faint():
                self.put_record_other(f"全ポケモンひんしのため終了")
                return FieldPhase.GAME_END
            else:
                self.put_record_other(f"ひんしのため交代が必要")
                return FieldPhase.FAINT_CHANGE
        else:
            return None

    def _is_any_faint(self) -> bool:
        """
        場に出ているポケモンがひんしになっているかどうか
        :return:
        """
        return any(map(lambda poke: poke.is_faint(), self._get_fighting_pokes()))

    def _is_all_faint(self) -> bool:
        """
        いずれかのプレイヤーのポケモンがすべてひんしになっているかどうか
        :return:
        """
        for party in self.parties:
            if all(map(lambda poke: poke.is_faint(), party.pokes)):
                return True
        return False
