"""
ポケモンの動的な状態
"""
import warnings
from typing import List, TypeVar, Optional
from enum import Enum

import pokeai.sim
from pokeai.sim.move_flag_db import move_flag_db
from pokeai.sim.poke_param_db import poke_param_db
from pokeai.sim.poke_static import PokeStatic
from pokeai.sim.move import Move
from pokeai.sim.poke_type import PokeType


class PokeNVCondition(Enum):
    """
    交代しても変化しない状態異常
    NV=Non Volatile
    """
    EMPTY = 1
    POISON = 2
    PARALYSIS = 3
    BURN = 4
    SLEEP = 5
    FREEZE = 6


class PokeMoveStatus:
    """
    ポケモンの覚えている技とその状態（PP等）
    """
    move: Move
    pp: int
    # TODO: かなしばり状態


class Rank:
    """
    ランクパラメータ
    """
    _value: int
    min: int
    max: int

    def __init__(self, min: int = -6, max: int = 6):
        self._value = 0
        self.min = min
        self.max = max

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int):
        assert self.min <= value <= self.max
        self._value = value

    def reset(self):
        self._value = 0

    def incr(self, diff: int):
        """
        パラメータを指定した数変動させる。最大値・最小値でクリッピングする。
        :param diff:
        :return:
        """
        self._value = max(min(self.value + diff, self.max), self.min)

    def can_incr(self, diff: int) -> bool:
        """
        ランクを指定した値だけ移動可能かどうかを返す。
        一部だけ移動できる場合もTrue。ランク5から+2 -> True
        :param diff:
        :return:
        """
        assert diff != 0
        if diff > 0:
            return self.value < self.max
        elif diff < 0:
            return self.value > self.min

    def scale_abcs(self, raw_value: int) -> int:
        """
        A,B,C,Sの値をランクでスケーリングする。
        :param raw_value: 補正前の値。
        :return:
        """
        if self.value >= 0:
            return raw_value * (self.value + 2) // 2
        else:
            return raw_value * 2 // (2 - self.value)


class Poke:
    """
    ポケモンの動的な状態
    """

    _poke_st: PokeStatic
    """
    基本ステータス
    """
    max_hp: int
    _hp: int
    st_a: int
    st_b: int
    st_c: int
    st_s: int
    base_s: int
    lv: int
    moves: List[PokeMoveStatus]
    poke_types: List[PokeType]
    """
    ランク補正
    """
    rank_a: Rank
    rank_b: Rank
    rank_c: Rank
    rank_s: Rank
    rank_evasion: Rank  # 回避
    rank_accuracy: Rank  # 命中
    multi_turn_move_info: TypeVar("pokeai.sim.multi_turn_move_info.MultiTurnMoveInfo")
    """
    状態異常
    """
    _nv_condition: PokeNVCondition
    _sleep_remaining_turn: int
    """
    状態変化(v_*)
    """
    _v_dig: bool
    _v_hyperbeam: bool
    _v_flinch: bool  # ひるみ
    _v_confuse_remaining_turn: int  # こんらん残りターン
    _v_badly_poison: bool
    _v_badly_poison_turn: int
    _v_leechseed: bool
    """
    最終発動技(当たるかにかかわらないが、眠りなどで発動しないときは更新されない)
    勝敗判定でのだいばくはつ利用判定に使用
    """
    last_move: Optional[Move]

    def __init__(self, poke_st: PokeStatic):
        self._poke_st = poke_st
        self.reset()

    def reset(self):
        # 静的パラメータをすべてコピー
        # 「へんしん」「テクスチャー」等でバトル中に書き換わりうる
        st = self._poke_st
        self.max_hp = st.max_hp
        self._hp = st.max_hp
        self.base_s = st.base_s
        self.st_a = st.st_a
        self.st_b = st.st_b
        self.st_c = st.st_c
        self.st_s = st.st_s
        self.lv = st.lv
        self.moves = []
        self.multi_turn_move_info = None
        for move in st.moves:
            pms = PokeMoveStatus()
            pms.move = move
            pms.pp = 5
            self.moves.append(pms)
        self.poke_types = self._poke_st.poke_types.copy()

        self.rank_a = Rank()
        self.rank_b = Rank()
        self.rank_c = Rank()
        self.rank_s = Rank()
        self.rank_accuracy = Rank(-6, 0)
        self.rank_evasion = Rank(0, 6)

        self._nv_condition = PokeNVCondition.EMPTY

        self._v_dig = False
        self._v_hyperbeam = False
        self._v_flinch = False
        self._sleep_remaining_turn = 0
        self._v_badly_poison = False
        self._v_badly_poison_turn = 0
        self._v_confuse_remaining_turn = 0
        self._v_leechseed = False

        self.last_move = None

    def on_change(self):
        """
        交代で戻ったときの処理
        :return:
        """
        self.rank_a.reset()
        self.rank_b.reset()
        self.rank_c.reset()
        self.rank_s.reset()
        self.rank_accuracy.reset()
        self.rank_evasion.reset()
        # 連続技途中での交代を想定していない（2世代以降の吹き飛ばし等、そういう技はないはず）
        assert self.multi_turn_move_info is None, "Poke.on_change called while continuous_move_info is not None"
        # 状態変化を解除
        self._v_dig = False
        self._v_hyperbeam = False
        self._v_flinch = False
        self._v_badly_poison = False
        self._v_badly_poison_turn = 0
        self._v_confuse_remaining_turn = 0
        self._v_leechseed = False
        self.last_move = None

    def on_turn_end(self):
        """
        ターン終了時の処理
        :return:
        """
        self._v_flinch = False

    def is_faint(self):
        return self.hp == 0

    @property
    def hp(self) -> int:
        return self._hp

    def hp_incr(self, diff: int):
        new_hp = self._hp + diff
        assert 0 <= new_hp <= self.max_hp
        self._hp = new_hp

    def eff_a(self, critical: bool = False) -> int:
        """
        補正済みこうげき
        :return:
        """
        val = self.st_a
        if critical:
            return val
        val = self.rank_a.scale_abcs(val)
        if self.nv_condition is PokeNVCondition.BURN:
            val = val // 2 - 1
        return val

    def eff_b(self, critical: bool = False) -> int:
        """
        補正済みぼうぎょ
        :return:
        """
        val = self.st_b
        if critical:
            return val
        val = self.rank_b.scale_abcs(val)
        return val

    def eff_c(self, critical: bool = False) -> int:
        """
        補正済みとくしゅ
        :return:
        """
        val = self.st_c
        if critical:
            return val
        val = self.rank_c.scale_abcs(val)
        return val

    def eff_s(self) -> int:
        """
        補正済みすばやさ
        :return:
        """
        val = self.st_s
        val = self.rank_s.scale_abcs(val)
        if self.nv_condition is PokeNVCondition.PARALYSIS:
            val //= 4
        return val

    def move_index(self, move: Move) -> int:
        """
        技からそのインデックスを取得
        :param move:
        :return:
        """
        for i, pms in enumerate(self.moves):
            if pms.move == move:
                return i
        raise ValueError

    def __str__(self):
        poke_param = poke_param_db[self._poke_st.dexno]
        s = f"{poke_param.names['ja']} (HP {self.hp}/{self.max_hp})\n"
        s += "  "
        for mi in self.moves:
            move_flag = move_flag_db[mi.move]
            s += f"{move_flag.names['ja']} "
        return s

    @property
    def nv_condition(self):
        """
        状態異常
        :return:
        """
        return self._nv_condition

    def update_nv_condition(self, cond: PokeNVCondition, *, sleep_turn: Optional[int] = None,
                            force_sleep: bool = False, badly_poison: bool = False):
        """
        状態異常の変化。各種フラグが連動して変化する。
        :param cond:
        :param force_sleep: 「ねむる」で状態異常にかかわらずねむる場合
        :param badly_poison: 猛毒状態にする
        :return:
        """
        if not force_sleep and (self._nv_condition != PokeNVCondition.EMPTY and cond != PokeNVCondition.EMPTY):
            # 状態異常の時の他の状態異常になろうとしているのは間違い
            raise ValueError
        if cond is PokeNVCondition.SLEEP:
            assert sleep_turn is not None
            self._sleep_remaining_turn = sleep_turn
        else:
            self._sleep_remaining_turn = 0
        if cond is PokeNVCondition.POISON and badly_poison:
            self.badly_poison = True
            self.badly_poison_turn = 0
        else:
            self.badly_poison = False
            self.badly_poison_turn = 0
        self._nv_condition = cond

    @property
    def sleep_remaining_turn(self):
        """
        ねむり状態残りターン
        :return:
        """
        return self._sleep_remaining_turn

    @sleep_remaining_turn.setter
    def sleep_remaining_turn(self, t: int):
        assert t >= 0
        self._sleep_remaining_turn = t

    @property
    def badly_poison(self):
        """
        猛毒フラグ
        :return:
        """
        return self._v_badly_poison

    @badly_poison.setter
    def badly_poison(self, v: bool):
        self._v_badly_poison = v

    @property
    def badly_poison_turn(self):
        """
        もうどく経過ターン
        :return:
        """
        return self._v_badly_poison_turn

    @badly_poison_turn.setter
    def badly_poison_turn(self, t: int):
        assert t >= 0
        self._v_badly_poison_turn = t

    @property
    def v_dig(self):
        """
        あなをほる状態
        :return:
        """
        return self._v_dig

    @v_dig.setter
    def v_dig(self, v: bool):
        self._v_dig = v

    @property
    def v_hyperbeam(self):
        """
        はかいこうせんの反動状態
        :return:
        """
        return self._v_hyperbeam

    @v_hyperbeam.setter
    def v_hyperbeam(self, v: bool):
        self._v_hyperbeam = v

    @property
    def v_flinch(self):
        """
        ひるみ状態
        ターン終了で解除される
        :return:
        """
        return self._v_flinch

    @v_flinch.setter
    def v_flinch(self, v: bool):
        self._v_flinch = v

    @property
    def v_confuse(self) -> bool:
        """
        混乱状態かどうか取得する。
        _v_confuse_remaining_turnから計算される。
        :return:
        """
        return self._v_confuse_remaining_turn > 0

    @property
    def v_confuse_remaining_turn(self):
        return self._v_confuse_remaining_turn

    @v_confuse_remaining_turn.setter
    def v_confuse_remaining_turn(self, value: int):
        self._v_confuse_remaining_turn = value

    @property
    def v_leechseed(self):
        """
        やどりぎ状態
        :return:
        """
        return self._v_leechseed

    @v_leechseed.setter
    def v_leechseed(self, v: bool):
        self._v_leechseed = v

    def can_change(self) -> bool:
        """
        自発的な交代が可能な状態かどうか判定する。
        はかいこうせんの反動状態などでは交代できない。
        :return:
        """
        if self.multi_turn_move_info is not None:
            return False
        if self._v_hyperbeam:
            return False
        return True
