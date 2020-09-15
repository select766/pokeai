# 汎用行動選択モデルの教師あり学習と強化学習の比較

2020年9月時点。

2020年3月まではパーティと、パーティ1つに対応するエージェントを保存していたが、エージェントが任意のパーティに対応するようになったため、学習したモデルはTrainerという名前で保存するように変更した。mongodbのDB名を`pokeai_2`から`pokeai_3`に変更している。

多数のコマンドを実行したりDBの中身を整形したりする処理が必要なのでjupyter notebookを添付。`ipynb_202009`内にある。

# 強化学習
パーティ生成（ランダム）

```
python -m pokeai.ai.generate_party good_200614_1 -r finalgoodmove1vs1
```

# 教師あり学習モデルの変換

2020年3月時点の教師あり学習モデルを、強化学習結果であるかのように無理やり変換する実装を用いる。

```
python -m pokeai.ai.generic_move_model.convert_supervised_to_trainer
```

# 強化学習と教師あり学習の比較

強化学習で学習に使ったパーティ群上でレーティングバトル
```
python -m pokeai.ai.generic_move_model.rl_rating_battle 5ee6075a3d6c05bcf736e7cf,5ee60e21f420ac034d11d316,#random good_200614_1
```

結果の評価は`display_high_rate_party_20200614_1-rl_vs_supervised.ipynb`参照

強化学習で学習に使わなかったパーティ群上でのレーティングバトル

```
python -m pokeai.ai.generate_party good_200614_3 -r finalgoodmove1vs1
python -m pokeai.ai.generic_move_model.rl_rating_battle 5ee6075a3d6c05bcf736e7cf,5ee60e21f420ac034d11d316,#random good_200614_3
```

結果の評価は`display_high_rate_party_20200614_1-rl_vs_supervised2.ipynb`参照

# 強化学習ハイパラチューニング
DB準備
```
optuna create-study --study-name rl_hyperparam_200801_10k --storage sqlite:///D:\dev\pokeai\pokeai\experiment\gmm\rl\hyperparam_tuning_200801\optuna.db
```

以下のコマンドをコア数だけ実行
```
python -m pokeai.ai.generic_move_model.optimize_rl_param D:\dev\pokeai\pokeai\experiment\gmm\rl\hyperparam_tuning_200801 --study_name rl_hyperparam_200801_10k --storage sqlite:///D:\dev\pokeai\pokeai\experiment\gmm\rl\hyperparam_tuning_200801\optuna.db --n_trials 50
```

事前に行列計算がシングルコアしか使わないように設定することを推奨
```cmd
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
```

結果の評価は`optuna_rl_analayze_200815-book.ipynb`参照

# 山登り法ペナルティの比較

```
python -m pokeai.ai.party_feature.hillclimb_party <trainer_id> <dst_tags> -r finalgoodmove1vs1 -n 1000 --party_feature_penalty <party_feature_penalty>
```

`<party_feature_penalty>`を0.0, 0.1, 1.0, 10.0に変化させ、生成されたパーティを定性的に比較する。

結果の評価は`hillclimb_result_200815-blog.ipynb`参照

# 強化学習とパーティ生成を交互に行う

* ループ学習用のバッチファイルを生成する:`loop_training_bat_gen_200815.ipynb`
* 学習結果、出来たパーティの統計値を確認:`hillclimb_result_200815_loop-blog.ipynb`
* 各反復内でのレーティングバトル:`rate_each_group_200815.ipynb`
* レーティングバトルで強かったパーティのID収集:`gather_high_rate_party_200815.ipynb`
* 強かったパーティの全反復混合レーティングバトル: `python -m pokeai.ai.generic_move_model.rl_rating_battle "" "" --player_ids_file D:\dev\pokeai\pokeai\experiment\gmm\rl\rl_loop_200815\top_player_ids.json`
* レーティングバトル結果確認: `display_high_rate_party_loop_200815_blog.ipynb`
* 各ターンの行動などのログを出力しながらレーティングバトル: `python -m pokeai.ai.generic_move_model.rl_rating_battle "" "" --player_ids_file D:\dev\pokeai\pokeai\experiment\gmm\rl\rl_loop_200815\top_player_ids.json --loglevel DEBUG 2>D:\dev\pokeai\pokeai\experiment\gmm\rl\rl_loop_200815\top_player_rating_battle.log`
* バトルログを目視確認: `visualize_battle_choice_rl-rating_200815_tops_blog.ipynb`

# カビゴン抜きルール

「強化学習とパーティ生成を交互に行う」の実験において、`regulation`を`finalgoodmove1vs1`から`finalgoodmove1vs1wosnorlax`に変更する。(snorlax=カビゴン)
