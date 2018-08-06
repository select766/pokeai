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

ランダムなパーティ構成(random pool)を1000個生成
```
python -m pokeai.agent.make_random_pool random_1k.bin 1000
```

パーティ同士をランダムに対戦させてレーティングを測定(どの技を選ぶかはランダム)
```
python -m pokeai.agent.rate_random_policy random_1k_rate.bin random_1k.bin
```

## 山登り法でパーティ生成
山登り法を用いて、ランダム生成よりも強いパーティを生成する。

山登り法にて強いパーティ構成を生成。強さ測定の対戦相手は`random_1k.bin`。
`--iter N`はパーティ構成を少し変えて強さを測定し、最強のものを選択する作業をN回繰り返すことを示す。
```
python -m pokeai.agent.hill_climbing hc_epoch1_1k.bin random_1k.bin random_1k_rate.bin 1000 --iter 30 --history
```

上で作成したパーティ同士を戦わせてレーティングを測定
```
python -m pokeai.agent.rate_random_policy hc_epoch1_1k_rate.bin hc_epoch1_1k.bin
```

## バトル中の方策の強化学習
(コード更新中につき現在動かない)

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
