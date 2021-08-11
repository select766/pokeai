# 第1世代ブランチの動かし方

環境構築自体はREADME.md参照

## パーティランダム生成
```
python -m pokeai.ai.generate_party foo -n 1000 -r gen1
```

1000個のパーティが、`gen1`ルールで生成され、`foo`というタグをつけて保存される。保存先はmongodb。

ルールは`data/dataset/regulations`内のディレクトリを指す

### 保存されるパーティの形式
```json
{
  "party": "<パーティ本体>",
  "tags": ["foo"]
}
```

パーティ本体は、Showdownのパーティフォーマットに準拠。

パーティのフォーマット

```json5
[
  {
    "name": "beedrill", //名前（種族名と違う値を指定したらどうなるのか未検証）
    "species": "beedrill", //種族名
    "moves": ["rage", "focusenergy", "bide", "pinmissile"], // 技リスト
    "ability": "No Ability", // 特性なし
    "evs": { // 努力値
      "hp": 255,
      "atk": 255,
      "def": 255,
      "spa": 255,
      "spd": 255,
      "spe": 255
    },
    "ivs": { // 個体値（最大30）
      "hp": 30,
      "atk": 30,
      "def": 30,
      "spa": 30,
      "spd": 30,
      "spe": 30
    },
    "item": "", // 持ち物なし
    "level": 50, // レベル
    "shiny": false, // 色違い
    "gender": "N", // 性別（第1世代では"N"のみ）
    "nature": "" // 性格
  },
  {
    "name": "jynx",
    "species": "jynx",
    "moves": ["seismictoss", "toxic", "watergun", "lick"],
    "ability": "No Ability",
    "evs": {
      "hp": 255,
      "atk": 255,
      "def": 255,
      "spa": 255,
      "spd": 255,
      "spe": 255
    },
    "ivs": {
      "hp": 30,
      "atk": 30,
      "def": 30,
      "spa": 30,
      "spd": 30,
      "spe": 30
    },
    "item": "",
    "level": 55,
    "shiny": false,
    "gender": "N",
    "nature": ""
  },
  {
    "name": "grimer",
    "species": "grimer",
    "moves": ["fireblast", "poisongas", "rage", "doubleteam"],
    "ability": "No Ability",
    "evs": {
      "hp": 255,
      "atk": 255,
      "def": 255,
      "spa": 255,
      "spd": 255,
      "spe": 255
    },
    "ivs": {
      "hp": 30,
      "atk": 30,
      "def": 30,
      "spa": 30,
      "spd": 30,
      "spe": 30
    },
    "item": "",
    "level": 50,
    "shiny": false,
    "gender": "N",
    "nature": ""
  }
]
```

# ランダム戦略でパーティ同士を対戦させ、レートを付与する
```
python -m pokeai.ai.generic_move_model.rl_rating_battle #random foo
```

デフォルトでは、1パーティ当たり100回対戦する。100ターンで決着がつかないと引き分け（レート変動なし）となる。

`--log gen1\sample\random_battle.log --loglevel DEBUG`を指定するとシミュレータとの通信内容がすべて出力されるが、ログファイルがかなり大きくなるので注意。1000パーティ、各100対戦で30GB程度になる。

コマンド実行すると以下のようなメッセージが出るので、メモする
```
rate_id: 6114025781a3542e844b3179
```

mongodbの`Rate`コレクションにこのIDで各パーティのレートが保存される。

結果を読み取って、パーティのランキングを表示するサンプル→`display_high_rate_party.ipynb`
