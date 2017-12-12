# -*- coding:utf-8 -*-

from enum import Enum, auto
from .poke_type import PokeType
from .poke_static_param import PokeStaticParam


class Poke(object):
    """description of class"""
    static_param: PokeStaticParam

    def __init__(self, static_param: PokeStaticParam):
        assert isinstance(static_param, PokeStaticParam)
        self.static_param = static_param
        self.reset_all()

    def eff_a(self, critical=False):
        """
        補正済みこうげき
        ランク・やけど
        (リフレクターは含まず)
        """
        st = self.static_param.st_a
        rank = self.rank_a
        if critical:
            return st
        st = st * _rank_table[rank] // 100
        if self.nv_condition is PokeNVCondition.Burn:
            st = st // 2
        return st

    def eff_b(self, critical=False):
        """
        補正済みぼうぎょ
        ランク
        (リフレクターは含まず)
        """
        st = self.static_param.st_b
        rank = self.rank_b
        if critical:
            return st
        st = st * _rank_table[rank] // 100
        return st

    def eff_c(self, critical=False):
        """
        補正済みとくしゅ
        ランク
        (リフレクターは含まず)
        """
        st = self.static_param.st_c
        rank = self.rank_c
        if critical:
            return st
        st = st * _rank_table[rank] // 100
        return st

    def eff_s(self):
        """
        補正済みすばやさ
        ランク・まひ
        (リフレクターは含まず)
        """
        st = self.static_param.st_s
        rank = self.rank_s
        st = st * _rank_table[rank] // 100
        if self.nv_condition is PokeNVCondition.Paralysis:
            st = st // 4
        return st

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        value = max(0, min(self.static_param.max_hp, value))
        self._hp = value

    @property
    def rank_a(self):
        return self._rank_a

    @rank_a.setter
    def rank_a(self, value):
        self._rank_a = max(-6, min(6, value))

    @property
    def rank_b(self):
        return self._rank_b

    @rank_b.setter
    def rank_b(self, value):
        self._rank_b = max(-6, min(6, value))

    @property
    def rank_c(self):
        return self._rank_c

    @rank_c.setter
    def rank_c(self, value):
        self._rank_c = max(-6, min(6, value))

    @property
    def rank_s(self):
        return self._rank_s

    @rank_s.setter
    def rank_s(self, value):
        self._rank_s = max(-6, min(6, value))

    @property
    def rank_accuracy(self):
        return self._rank_accuracy

    @rank_accuracy.setter
    def rank_accuracy(self, value):
        self._rank_accuracy = max(-6, min(0, value))

    @property
    def rank_evasion(self):
        return self._rank_evasion

    @rank_evasion.setter
    def rank_evasion(self, value):
        self._rank_evasion = max(0, min(6, value))

    @property
    def can_poisoned(self):
        """
        新たに毒状態になれるか
        """
        if self.nv_condition is not PokeNVCondition.Empty:
            return False
        if PokeType.Poison in [self.type1, self.type2]:
            return False
        return True

    @property
    def can_paralyzed(self):
        """
        新たにまひ状態になれるか
        """
        if self.nv_condition is not PokeNVCondition.Empty:
            return False
        return True

    @property
    def can_burned(self):
        """
        新たにやけど状態になれるか
        """
        if self.nv_condition is not PokeNVCondition.Empty:
            return False
        if PokeType.Fire in [self.type1, self.type2]:
            return False
        return True

    @property
    def can_sleep(self):
        """
        新たにねむり状態になれるか
        """
        if self.nv_condition is not PokeNVCondition.Empty:
            return False
        return True

    @property
    def can_freezed(self):
        """
        新たにこおり状態になれるか
        """
        if self.nv_condition is not PokeNVCondition.Empty:
            return False
        if PokeType.Ice in [self.type1, self.type2]:
            return False
        return True

    @property
    def is_faint(self):
        return self._hp == 0

    def reset_all(self):
        self.reset_volatile()
        self.reset_nonvolatile()

    def reset_volatile(self):
        """
        ひっこめると治るパラメータのリセット
        """
        self.move_handler = None
        self._rank_a = 0
        self._rank_b = 0
        self._rank_c = 0
        self._rank_s = 0
        self._rank_evasion = 0
        self._rank_accuracy = 0
        self.confusion_turn = 0
        # もうどくは普通のどくになる
        self.bad_poison = False
        self.bad_poison_turn = 0
        # リフレクター状態(防御ランクとは別)
        self.reflect = False
        # あなをほる状態
        self.digging = False

        # 「テクスチャー」があるのでタイプは変動しうる
        self.type1 = self.static_param.type1
        self.type2 = self.static_param.type2

    def reset_nonvolatile(self):
        """
        ひっこめても治らないパラメータのリセット
        """
        self._hp = self.static_param.max_hp
        self.nv_condition = PokeNVCondition.Empty
        self.sleep_turn = 0

    def reset_turn_end(self):
        """
        ターン終了でリセットされるパラメータのリセット
        """
        # TODO: ひるみ

    def calc_ratio_damage(self, ratio_x16):
        """
        最大HPとの割合ダメージの計算
        """
        return self.static_param.max_hp * ratio_x16 // 16

    def __str__(self):
        return "{}".format(self.static_param.dexno)

    def __repr__(self):
        s = "{};HP={}/{}".format(self.static_param.dexno,
                                 self.hp, self.static_param.max_hp)
        if self.nv_condition is not PokeNVCondition.Empty:
            s += ";{}".format(self.nv_condition.name)
        if self.move_handler is not None:
            s += ";{}".format(self.move_handler.move_entry.move_id.name)
        return s

    def render(self, static_only=True):
        """
        ポケモンのパラメータを表示する
        :param static_only: 対戦中に変動しないパラメータのみ表示
        :return:
        """
        assert static_only  # not implemented
        print(f"{self.static_param.dexno};HP={self.hp};Moves={self.static_param.move_ids}")


class PokeNVCondition(Enum):
    """
    交代しても変化しない状態異常
    """
    Empty = 1
    Poison = 2
    Paralysis = 3
    Burn = 4
    Sleep = 5
    Freeze = 6


# https://wiki.ポケモン.com/wiki/%E3%83%A9%E3%83%B3%E3%82%AF%E8%A3%9C%E6%AD%A3
_rank_table = {-6: 25, -5: 28, -4: 33, -3: 40, -2: 50, -1: 66,
               0: 100, 1: 150, 2: 200, 3: 250, 4: 300, 5: 350, 6: 400}
