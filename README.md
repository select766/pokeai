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

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。
