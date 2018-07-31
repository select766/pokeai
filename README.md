# PokéAI ～人工知能の考えた最強のポケモン対戦戦略～
PokéAI(ポケエーアイ)は、ポケモンバトルの戦略を人工知能に考えさせ、
究極的には人が思いつかなかったような戦略を編み出すことを目標とするプロジェクトです。

初代バージョンの全ポケモン・技実装用ブランチ。2017年時点のコードをいったん消して再構築中。

# setup
Python 3.6が必要。

```
python setup.py develop
```

# test
```
python -m unittest
```

# AI機能
## ランダムなパーティ・方策での対戦
ランダムなパーティ構成(random pool)と対戦結果(レーティング)を保存
```
python -m pokeai.agent.make_random_pool OUTPUT_FILE_NAME N_PARTIES
```

## 山登り法でパーティ生成
山登り法を用いて、ランダム生成よりも強いパーティを生成する。
```
python -m pokeai.agent.hill_climbing OUTPUT_FILE_NAME RANDOM_POOL_FILE
```

## バトル中の方策の強化学習
適宜出力ディレクトリ作成

プレイヤー、学習時の敵、テスト時の敵パーティの生成
```
python -m pokeai.agent.make_random_pool policy_train\random_pool_friend_1k.bin 1000
python -m pokeai.agent.make_random_pool policy_train\random_pool_train_10k.bin 10000
python -m pokeai.agent.make_random_pool policy_train\random_pool_test_1k.bin 1000
```

方策の学習
```
python -m pokeai.agent.train_battle_policy policy_train\agents1 policy_train\random_pool_friend_1k.bin policy_train\random_pool_train_10k.bin --count 10
```

`--count 10`は10パーティについてそれぞれ方策を学習する。(今のところ、自分のパーティが違えば独立したモデルを学習する)

学習した方策のレーティング評価(ランダム方策、同じ技を出し続ける方策と比較)
```
python -m pokeai.agent.test_battle_policy policy_train\agents1 policy_train\random_pool_friend_1k.bin policy_train\random_pool_test_1k.bin --count 10
```

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。
