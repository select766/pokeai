from abc import ABCMeta, abstractmethod
from typing import TypedDict, List

# 努力値、個体値を表すdict (defが予約語のためこの定義方法)
PokeEvIv = TypedDict('PokeEvIv', {'hp': int, 'atk': int, 'def': int, 'spa': int, 'spd': int, 'spe': int})


class PartyPoke(TypedDict):
    name: str  # 名前(任意)
    species: str  # ポケモン種族名
    moves: List[str]  # 技一覧
    ability: str  # 特性 第2世代では'No Ability'
    evs: PokeEvIv  # max: 255
    ivs: PokeEvIv  # max: 30
    item: str  # 所持アイテム なし=''
    level: int  # レベル
    shiny: bool  # 色違い 個体値との整合性がチェックされるため常にFalse
    gender: str  # 性別 オス='M', メス='F', 不明='N' 個体値依存のため性別固定以外はオスとする
    nature: str  # 性格 第2世代では''


Party = List[PartyPoke]


class PartyGenerator(metaclass=ABCMeta):
    @abstractmethod
    def generate(self) -> Party:
        raise NotImplementedError

    @abstractmethod
    def neighbor(self, party: Party) -> Party:
        raise NotImplementedError
