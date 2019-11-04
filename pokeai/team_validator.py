import os
import subprocess
import json
from typing import Optional, List
from pokeai.simutil import sim_util


class TeamValidator:
    def validate(self, party) -> Optional[List[str]]:
        return sim_util.call('validateTeam', {'party': party})


def demo():
    # 技などが覚えられるか判定
    validator = TeamValidator()
    fill = {
        'name': 'XXX',
        "ability": 'No Ability',
        "evs":
            {"hp": 255, "atk": 255, "def": 255, "spa": 255, "spd": 255, "spe": 255},
        "ivs": {"hp": 30, "atk": 30, "def": 30, "spa": 30, "spd": 30, "spe": 30},
        "item": 'Leftovers',
        "level": 55,
        "shiny": False,  # 色違いと個体値の関係はチェックされる
        "gender": 'M',
        "nature": ''}
    parties = [
        [{**fill,
          "species": "tyranitar",  # バンギラス
          "moves": ['leer'],  # にらみつける
          }],
        # ポケモン、持ち物の重複は検査しない
        [{**fill,
          "species": "tyranitar",
          "moves": ['leer'],
          },
         {**fill,
          "species": "tyranitar",
          "moves": ['leer'],
          }],
        [{**fill,
          "species": "tyranitar",
          "moves": ['leer'],
          "gender": "F",  # 個体値と性別の不一致はエラー
          }],
        [{**fill,
          "species": "tyranitar",
          "moves": ['leer'],
          "level": 50,  # LV50のバンギラスは存在しないのでエラー
          }],
        [{**fill,
          "species": "moltres",  # ファイヤー
          "moves": ['leer'],
          "level": 50,  # LV50ではにらみつけるを覚えないのでエラー
          }],
        [{**fill,
          "species": "moltres",  # ファイヤー
          "moves": ['leer'],
          "level": 51,  # LV51ではにらみつけるを覚えるのでOK
          }],
        [{**fill,
          "species": "bulbasaur",  # フシギダネ
          "moves": ['safeguard'],  # 卵技しんぴのまもり
          }],
        [{**fill,
          "species": "bulbasaur",  # フシギダネ
          "moves": ['swordsdance'],  # 第1世代限定技マシンつるぎのまい
          }],
        [{**fill,
          "species": "bulbasaur",  # フシギダネ
          "moves": ['safeguard', 'swordsdance'],  # 第1世代に存在しない卵技と第1世代限定技マシンの両立不可でエラー
          }],
        [{**fill,
          "species": "bulbasaur",  # フシギダネ
          "moves": ['lightscreen', 'swordsdance'],  # 卵技ひかりのかべ(第1世代に存在)と第1世代限定技マシンつるぎのまい=>OK
          }],
        [{**fill,
          "species": "bulbasaur",  # フシギダネ
          "moves": ['lightscreen', 'swordsdance'],  # 卵技ひかりのかべ(第1世代に存在)と第1世代限定技マシンつるぎのまい=>OK
          }],
        [{**fill,
          "species": "espeon",  # エーフィ
          "moves": ['skullbash', 'psychic'],  # 第1世代限定技マシンロケットずつきと第2世代限定の進化系=>OK
          }],
        [{**fill,
          "species": "blissey",  # ハピナス
          "moves": ['thunderbolt'],  # 10まんボルト(クリスタル限定教え技)
          "gender": "M"  # メスしかいないので本来エラーなのだが通過する
          }],
        [{**fill,
          "species": "blissey",  # ハピナス
          "moves": ['thunderbolt'],  # 10まんボルト(クリスタル限定教え技)
          "gender": "F"
          }],
    ]
    # その他
    # 性別不明ポケモンの性別は検査しない
    for party in parties:
        print("party", party)
        print("result", validator.validate(party))


if __name__ == '__main__':
    demo()
