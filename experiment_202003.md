# PokéAI 3.5巻 (2020年3月)対応学習方法
パーティ固有モデルでの強化学習結果を用いて対戦、そのログを教師として汎用行動選択モデルを学習。

tag: book-202003 (41b45b979b0e8f667532c2a7d4145e775218d290)に対応。それ以降非互換なコミットが入っているので注意。
requriments.txtに入ってないが、`torch==1.4.0`が必要。またmongodbも必要。

具体的なコマンドが一部残っておらず申し訳ありません。

# 「まともな技」セットの作成
最終進化系ポケモン、1vs1、すべての技を含むレギュレーションが`final1vs1`。

ここから、AIが運用できそうなまともな技を抽出する。

レギュレーション上でランダム行動で対戦

```
python -m pokeai.ai.generate_party final_random_200206_1 -n 10000 -r final1vs1
python -m pokeai.ai.assign_random_policy final_random_200206_1 final_random_200206_1_r
python -m pokeai.ai.rating_battle final_random_200206_1_r
```



M特徴のみでパーティ評価関数の学習

`experiment\gmm\config\prp_config_m.yaml`:
```yaml
feature_params:
  names:
    - M
regressor_params:
  C: 0.01
```

```
python -m pokeai.ai.party_feature.train_party_rate_predictor experiment\gmm\config\prp_config_m.yaml 5e3bec289fbf91b3d0fef5bf experiment\gmm\model\prp_config_m --crossval 5
```

ここから`final1vs1`に含まれる各ポケモンについて、覚えられる技のうち係数上位8つの技を選択。全ポケモンについて和集合を計算。その結果、52個の技が選択された。
結果は`finalgoodmove1vs1`レギュレーションとして保存。（コマンドなし）

# パーティごとの強化学習

パーティ生成・ランダム行動エージェントを付与
```
python -m pokeai.ai.generate_party fgm_random_200207_2 -n 1000 -r finalgoodmove1vs1
python -m pokeai.ai.assign_random_policy fgm_random_200207_2 fgm_random_200207_2_r
```

設定ファイルを設置

`experiment\gmm\config\agent_params_linear_v2_13.yaml`:
```yaml
version: 2
model:
    type: ACERSeparateModel
    pi:
        kwargs:
            n_hidden_layers: 0
            n_hidden_channels: 32
    q:
        kwargs:
            n_hidden_layers: 0
            n_hidden_channels: 32
optimizer:
    kwargs:
        alpha: 1.0e-2
agent:
    type: ACER
    kwargs:
        gamma: 0.99
        replay_start_size: 1000
replay_buffer:
    kwargs:
        capacity: 10000
```

`experiment\gmm\config\feature_params_1vs1.yaml`:
```yaml
feature_types:
  - remaining_count
  - poke_type
  - hp_ratio
  - nv_condition
  - rank
  - weather
party_size: 1
```

各パーティを、ランダム行動エージェントを相手に強化学習
```
python -m pokeai.ai.acer_train <party_id> fgm_random_200207_2_r experiment\gmm\config\feature_params_1vs1.yaml experiment\gmm\config\agent_params_linear_v2_13.yaml acer_200207_2 --battles 1000  --step_agent_tags acer_200207_2_s --save_step 100
```

`<party_id>`はmongodbを見てパーティのIDに置き換え、全パーティ分実行が必要。1パーティあたり5分程度。

# レーティングバトルによる教師データ作成
教師あり学習の教師となる、各パーティの行動を出力

```
python -m pokeai.ai.rating_battle acer_200207_2 --loglevel DEBUG --match_count 100 2> experiment\gmm\log\rating_battle_acer_200207_2.log
```

ログファイルは2GB程度になる。

ログから各ターンの状態とエージェントがとった行動を抽出

```
python -m pokeai.ai.generic_move_model.extract_log experiment\gmm\log\rating_battle_acer_200207_2.log experiment\gmm\dataset\rating_battle_acer_200207_2
```

ここで、エージェントをtrain/valに分けるためのテキストファイルを作成する。

`experiment\gmm\dataset\train.txt`:
```text
5e3e1a200883883d073b9588
5e3e330d30e32817df1a40dd
5e3d51a9dc47652c4a46c5d3
...
```
1行に1つエージェントIDを与える。`train.txt`は900行、`val.txt`は残りの100行。

特徴量ベクトルの抽出
```
python -m pokeai.ai.generic_move_model.preprocess_train_data experiment\gmm\dataset\rating_battle_acer_200207_2 experiment\gmm\dataset\train.txt experiment\gmm\dataset\train_feat
python -m pokeai.ai.generic_move_model.preprocess_train_data experiment\gmm\dataset\rating_battle_acer_200207_2 experiment\gmm\dataset\val.txt experiment\gmm\dataset\val_feat
```

# 教師あり学習
学習設定ファイルを作成する。(以下は一番うまくいったモデルの例。他の実験は`model.yaml`のパラメータのみ変更)

`experiment\gmm\train\200216_12\train.yaml`:
```yaml
optimizer:
  class: Adam
  kwargs:
    lr: 1.0e-2
epoch: 10
dataset:
  train:
    dir: experiment\gmm\dataset\train_feat
    batch_size: 256
  val:
    dir: experiment\gmm\dataset\val_feat
    batch_size: 256
```

`experiment\gmm\train\200216_12\model.yaml`:
```yaml
class: MLPModel
kwargs:
  n_layers: 3
  n_channels: 16
  bn: false
```

教師あり学習を実行
```
python -m pokeai.ai.generic_move_model.train_model experiment\gmm\train\200216_12 experiment\gmm\dataset\train_feat experiment\gmm\dataset\val_feat
```

学習結果のモデルを評価
```
python -m pokeai.ai.generic_move_model.train_model experiment\gmm\train\200216_12 --predict
```

各局面での行動選択確率が`pred.npz`に出力される。手動で分析が必要。
