# PokéAI ～人工知能の考えた最強のポケモン対戦戦略～
PokéAI(ポケエーアイ)は、ポケモンバトルの戦略を人工知能に考えさせ、
究極的には人が思いつかなかったような戦略を編み出すことを目標とするプロジェクトです。

現在、初代バージョン（赤・緑）のルールに取り組んでおり、最新のバージョンのゲームの対戦で役立つものではありませんのでご注意ください。

研究の結果は本(同人誌)の形態で発表し、このリポジトリは実験コードを置くためのものです。
コードは今後大規模に変更される予定なので、パッチ等は受け付けておりません。

本はこちらです。
- [準備編(2017-12-24)](https://github.com/select766/pokeai/releases/download/book-201712/PokeAI-201712.pdf)

PokéAI project is to make artificial intelligence devise strategy of Pokémon battle.
Hill climbing method is used for party generation and deep reinforcement learning method is used for action selection in battle.
The outcome of the research is released as fan publication (currently, Japanese only).

# 実験コード
備忘録としてコマンドとその意味を記載しておりますが、状況に応じた設定ファイル書き換えが必要です。
結果の可視化機能もないので、このまま実行しても実用性はありません。

## 環境
Windows 10 + Python 3.6環境です。ファイルパスの指定に一部"\"を使っていますが、そこを修正すればWindows以外でも動くはずです。

依存ライブラリのインストール
```
pip install -r requirements.txt
```

`pokeai`ライブラリをimport可能とする
```
python setup.py develop
```

## コマンド

ランダムなパーティ群生成
```
python -m pokeai.ai_v4.generate_random_pool data\parties\random_test_pool_100.pickle 100
```

山登り法+強化学習でのパーティ構築
```
python -m pokeai.ai_v4.train params\hill_climbing_rl.yaml params\party_loader.py
```
`data\hill_climbing_*`に構築されたパーティのファイルが書きだされる。

パーティ相互対戦(事前に設定ファイルに学習時の`run_id`を書き込む必要あり)
```
python -m pokeai.ai_v4.party_match params\party_group_20171217.yaml params\hill_climbing_rl.yaml
```
`data\party_match_*`に対戦結果のファイルが書きだされる。pickleを読んで解析する必要あり。

事前生成したパーティ群（ランダム行動）との対戦
```
python -m pokeai.ai_v4.party_match params\party_group_20171217.yaml params\hill_climbing_rl.yaml --enemy_parties data\parties\random_test_pool_100.pickle
```

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。
