from typing import Optional, List
from pokeai.sim.simutil import sim_util


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
          "gender": "F",  # 個体値と性別の不一致はエラー 'XXX (Tyranitar) must be at least level 55 to be evolved.'
          }],
        [{**fill,
          "species": "tyranitar",
          "moves": ['leer'],
          "level": 50,  # LV50のバンギラスは存在しないのでエラー 'XXX (Tyranitar) must be at least level 55 to be evolved.'
          }],
        [{**fill,
          "species": "moltres",  # ファイヤー
          "moves": ['leer'],
          "level": 50,  # LV50ではにらみつけるを覚えないのでエラー "XXX (Moltres)'s move Leer is learned at level 51."
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
          "moves": ['safeguard', 'swordsdance'],  # 第1世代に存在しない卵技と第1世代限定技マシンの両立不可でエラー "XXX (Bulbasaur)'s moves Safeguard, Swords Dance are incompatible."
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
          "species": "cubone",  # カラカラ
          "moves": ['perishsong', 'swordsdance'],  # 卵技ほろびのうた・つるぎのまい=>同時遺伝経路がない "XXX (Cubone) can't get its egg move combination (perishsong, swordsdance) from any possible father.", '(Is this incorrect? If so, post the chainbreeding instructions in Bug Reports)'
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
        [{**fill,
          "species": "blissey",  # ハピナス
          "moves": ['hiddenpower'],  # めざめるパワー（タイプ特定なし）: OK
          "gender": "F"
          }],
        [{**fill,
          "species": "blissey",  # ハピナス
          "moves": ['hiddenpowerice'],  # めざめるパワー（タイプ特定あり）: 個体値との矛盾はダメ, 'XXX has Hidden Power Ice, but its IVs are for Hidden Power Dark.'
          "gender": "F"
          }],
        [{**fill,
          "species": "blissey",  # ハピナス
          "moves": ['hiddenpowerdark'],  # めざめるパワー（タイプ特定あり）: 最大個体値なら悪
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
