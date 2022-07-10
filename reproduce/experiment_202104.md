# 汎用行動選択モデルの3vs3拡張の実験

2021年4月時点。

mongodbのDB名: `pokeai_4`

jupyter notebook: `ipynb_202104`

最終実験であるパーティ生成とモデル学習をループで行う方法について記載。

# パーティ生成とモデル学習をループで行う

`loop_training_bat_gen_20210227_1.ipynb` を用いて設定ファイルとバッチファイルを生成する。バッチファイルを実行することで学習が進む。

`rate_each_group_210227_1.ipynb` により各iteration内でのパーティの対戦を行い、レーティングを付与する。

# 分析

- iterごとポケモン出現頻度の表示 `hillclimb_result_210227_1-blog.ipynb`
- iterごと強かったパーティの表示 `display_high_rate_party_210227_1.ipynb`
- iterごと強かったパーティを抽出して、混合してバトルさせるためのトップパーティリストを生成 `gather_high_rate_party_210227_1.ipynb`

# トップパーティを対戦させる

```
python -m pokeai.ai.generic_move_model.rl_rating_battle "" "" --player_ids_file D:\dev\pokeai\pokeai\experiment\team\rl\rl_loop_210227_1\top_player_ids.json
```

- iterごとのレート平均、強かったパーティ表示 `display_high_rate_party_loop_210227_1_blog.ipynb`

# 定性評価用バトル

```
python -m pokeai.ai.generic_move_model.rl_rating_battle "" "" --player_ids_file D:\dev\pokeai\pokeai\experiment\team\rl\rl_loop_210227_1\top_player_ids.json --loglevel DEBUG --match_count 10 --log D:\dev\pokeai\pokeai\experiment\team\log\rl_loop_210227_1_tops_battles.log
```


ログファイルを `pokeai\ai\analysis\format_battle_log.py` にかけて、１バトル１行の形式にする。さらに `pokeai\ai\analysis\filter_battle_log.py` で指定したプレイヤーのバトルのみを抽出できる。

ログの可視化は `/visualize-battle-log` のreactプログラムを実行。ブラウザ上でログファイルを開く。 実際のログとして、 `rl_loop_210227_1_tops_battles.top10.zip` を解凍して開く。

# カビゴン抜きルール

「強化学習とパーティ生成を交互に行う」の実験において、`regulation`を`finalgoodmove3vs3`から`finalgoodmove3vs3wosnorlax`に変更する。(snorlax=カビゴン)
