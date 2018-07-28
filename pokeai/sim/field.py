from enum import Enum, auto
from typing import List, Optional, Callable, Dict, Tuple

from pokeai.sim.field_action import FieldAction, FieldActionType
from pokeai.sim.field_record import FieldRecord, FieldRecordReason
from pokeai.sim.game_rng import GameRNG, GameRNGRandom, GameRNGReason
from pokeai.sim.move import Move
from pokeai.sim.move_calculator import MoveCalculator
from pokeai.sim.party import Party
from pokeai.sim.poke import Poke, PokeNVCondition


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
    actions_faint_change: Optional[List[Optional[FieldAction]]]
    _phase_handlers: Dict[FieldPhase, Callable[[], FieldPhase]]
    winner: Optional[int]

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
            FieldPhase.FAINT_CHANGE: self._step_faint_change,
            FieldPhase.END_TURN: self._step_end_turn,
            FieldPhase.GAME_END: self._step_game_end,
        }
        self.rng = GameRNGRandom()
        self.rng.field = self
        self.first_player = None
        self.phase = FieldPhase.BEGIN
        self.winner = None

    def step(self) -> FieldPhase:
        """
        次にプレイヤーが操作可能になるまで進める
        :return:
        """
        while self._step_one() not in [FieldPhase.BEGIN, FieldPhase.FAINT_CHANGE, FieldPhase.GAME_END]:
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
            poke = self.parties[player].get()
            speed = poke.eff_s()
            if act.action_type is FieldActionType.CHANGE:
                # 交代は先攻
                speed += 10000
            else:
                move = poke.moves[act.move_idx].move
                if move in [Move.QUICKATTACK]:
                    # 優先度+1
                    speed += 1000
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
        for poke in self._get_fighting_pokes(0):
            # ここで倒れることは初代ではないので、順番は関係ない
            # ひるみ等解除
            poke.on_turn_end()
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
            attack_poke.on_change()  # 今のポケモンを控えに戻す
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
        if attack_poke.nv_condition is PokeNVCondition.BURN:
            # やけどダメージ
            damage = attack_poke.max_hp // 16
            die = False
            if damage >= attack_poke.hp:
                damage = attack_poke.hp
                die = True
            self.put_record_other(f"やけどダメージ {damage}")
            attack_poke.hp_incr(-damage)
            if die:
                return
        if attack_poke.nv_condition is PokeNVCondition.POISON:
            # どくダメージ
            damage = attack_poke.max_hp // 16
            if attack_poke.badly_poison:
                attack_poke.badly_poison_turn += 1
                damage *= attack_poke.badly_poison_turn
            die = False
            if damage >= attack_poke.hp:
                damage = attack_poke.hp
                die = True
            self.put_record_other(f"どくダメージ {damage}")
            attack_poke.hp_incr(-damage)
            if die:
                return
        if attack_poke.v_leechseed:
            # やどりぎダメージ=毒ダメージと同じ
            damage = attack_poke.max_hp // 16
            if attack_poke.badly_poison:
                # どくどくならダメージが増える
                damage *= attack_poke.badly_poison_turn
            die = False
            if damage >= attack_poke.hp:
                damage = attack_poke.hp
                die = True
            self.put_record_other(f"やどりぎダメージ {damage}")
            attack_poke.hp_incr(-damage)
            max_recover = defend_poke.max_hp - defend_poke.hp
            recover = min(max_recover, damage)
            defend_poke.hp_incr(recover)
            if die:
                return

    def _step_faint_change(self) -> FieldPhase:
        """
        ひんしになったポケモンの交代を行う
        :return:
        """
        for player, poke in enumerate(self._get_fighting_pokes()):
            action = self.actions_faint_change[player]
            if poke.is_faint():
                assert action.action_type is FieldActionType.FAINT_CHANGE
                self.parties[player].fighting_idx = action.faint_change_idx
                self.put_record_other(f"瀕死交代: Player {player} は {self.parties[player].get()} を繰り出した")
                assert not self.parties[player].get().is_faint()
            else:
                assert action is None
        return FieldPhase.BEGIN

    def _step_game_end(self):
        raise RuntimeError("step called when GAME_END")

    def _get_fighting_pokes(self, attack_player: int = 0) -> Tuple[Poke, Poke]:
        """
        攻撃側、守備側の場に出ているポケモンを取得する。
        引数なしならplayer0, player1の順。
        :param attack_player:
        :return:
        """
        defend_player = 1 - attack_player
        return self.parties[attack_player].get(), self.parties[defend_player].get()

    def get_legal_actions(self, player: int) -> List[FieldAction]:
        """
        この場で有効な行動を列挙する。
        :param player:
        :return:
        """
        # 控えの列挙
        alive_poke_idxs = []
        party = self.parties[player]
        for i, poke in enumerate(party.pokes):
            if i == party.fighting_idx:
                continue
            if poke.is_faint():
                continue
            alive_poke_idxs.append(i)

        if self.phase is FieldPhase.BEGIN:
            # 控えの列挙
            poke = party.get()
            multi_turn_move_index = None
            if poke.multi_turn_move_info is not None:
                # 連続技の最中はそれを選ぶ
                mt_move = poke.multi_turn_move_info.move
                for move_index, pms in enumerate(poke.moves):
                    if mt_move == pms.move:
                        multi_turn_move_index = move_index
                        break
            actions = []
            if multi_turn_move_index is not None:
                actions.append(FieldAction(FieldActionType.MOVE, move_idx=multi_turn_move_index))
            else:
                for move_index in range(len(poke.moves)):
                    actions.append(FieldAction(FieldActionType.MOVE, move_idx=move_index))

            if poke.can_change():
                for alive_poke_idx in alive_poke_idxs:
                    actions.append(FieldAction(FieldActionType.CHANGE, change_idx=alive_poke_idx))
        elif self.phase is FieldPhase.FAINT_CHANGE:
            actions = []
            poke = party.get()
            if poke.is_faint():
                for alive_poke_idx in alive_poke_idxs:
                    actions.append(FieldAction(FieldActionType.FAINT_CHANGE, faint_change_idx=alive_poke_idx))
            # ひんしでない側はアクションなし
        else:
            raise RuntimeError
        return actions

    def _get_next_phase_if_faint(self) -> Optional[FieldPhase]:
        """
        場に出ているポケモンがひんしになっていれば、次のphaseを返す。
        そうでなければNoneを返す。
        :return:
        """
        if self._is_any_faint():
            # 片方が全員ひんしならゲーム終了
            if self._is_all_faint():
                self.put_record_other(f"全ポケモンひんしのため終了")
                # 勝者を判定する
                self.winner = self._get_winner()
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

    def _get_winner(self) -> int:
        """
        どちらかがすべて倒れた時の勝敗の判定
        :return: 勝ったプレイヤーの番号。引き分けは存在しない。
        """
        # 片方だけすべて倒れているとき、倒れていない側の勝ち
        party_faint = []
        for party in self.parties:
            party_faint.append(all(map(lambda poke: poke.is_faint(), party.pokes)))
        if party_faint[0]:
            if party_faint[1]:
                # 両方倒れている
                # 先攻の攻撃直後なら、先攻の勝ち(反動で倒れても、攻撃側の勝ち)
                # 後攻の攻撃直後なら、後攻の勝ち
                # PCのときに両方倒れることはない
                win_player = 0
                if self.phase is FieldPhase.FIRST_MOVE:
                    win_player = self.first_player
                elif self.phase is FieldPhase.SECOND_MOVE:
                    win_player = 1 - self.first_player
                else:
                    raise NotImplementedError
                if self.parties[win_player].get().last_move in [Move.EXPLOSION, Move.SELFDESTRUCT]:
                    # 最終発動技が自爆技なら使ってない側の勝ち
                    win_player = 1 - win_player
                return win_player
            else:
                return 1
        else:
            assert party_faint[1]
            return 0
