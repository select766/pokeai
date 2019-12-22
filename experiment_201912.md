# パーティ生成・評価関数学習
## ランダムパーティ生成・バトルでレーティング
```
python -m pokeai.ai.generate_party random_191201_3 -n 10000
python -m pokeai.ai.assign_random_policy random_191201_3 random_191201_3_r
python -m pokeai.ai.rating_battle random_191201_3_r
```
`generate_party`で、パーティを生成。パーティはそれぞれ固有のランダムIDを持ち、さらにタグ`random_191201_3`が付与される。
`assign_random_policy`で、パーティに対しランダムに行動するエージェントを生成。エージェントはそれぞれ固有のランダムIDを持ち、1つのパーティに対応する。
ここではパーティタグ`random_191201_3`がついているパーティそれぞれに対してエージェントを生成し、それにエージェントタグ`random_191201_3_r`を付与。
`rating_battle`で、エージェントタグ`random_191201_3_r`が付与されたエージェントすべてを1つの環境で相互に対戦させ、それぞれのエージェントにレートを付与する。
実行後にrate idが表示される。このidから、エージェントとレートの対応を引き出せる。次にこの値を使用する。`=> rate id 5de382a05eb535102b30665c`

## パーティ評価関数の学習

`data/ai/pr/prp_config_1.yaml`を設置:
```yaml
feature_params:
  names:
    - P
    - M
    - I
    - PP
    - MM
    - PM
    - PI
    - MI
regressor_params:
  C: 0.01
```

```
python -m pokeai.ai.party_feature.train_party_rate_predictor data/ai/pr/prp_config_1.yaml 5de382a05eb535102b30665c data/ai/pr/prp_1_cv --limit 10000 --crossval 5
```

## パーティ評価関数に基づいたパーティ生成
```
python -m pokeai.ai.generate_party random_191202_1 -n 100
python -m pokeai.ai.party_feature.hillclimb_party data/ai/pr/prp_1_cv/party_rate_predictor.bin random_191202_1 hillclimb_191202_100_10 --generations 100 --populations 10
```

## 強化学習

強いパーティに対してランダムエージェントをくっつける
```
python -m pokeai.ai.assign_random_policy hillclimb_191202_100_10 hillclimb_191202_100_10_r
```

`data\tmp\agent_params_linear_v2_13.yaml`を設置:

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

```
python -m pokeai.ai.acer_train 5de46e1b1cb1e07bbc26f2cb hillclimb_191202_100_10_r data\tmp\agent_params_linear_v2_13.yaml acer_191209_13 --battles 1000 --step_agent_tags acer_191209_13_s --save_step 100
```
`5de46e1b1cb1e07bbc26f2cb`は学習対象のパーティのID。100パーティあったら100パーティ分別のIDを入れてこのコマンドを実行。

パーティのIDを列挙するpythonコードの例
```python
from pokeai.ai.party_db import col_party
party_ids = [d['_id'] for d in col_party.find({"tags": "hillclimb_191202_100_10"})]
```

## 評価
基準となるランダムパーティの生成・レーティング
```
python -m pokeai.ai.generate_party random_191203_1 -n 100
python -m pokeai.ai.assign_random_policy random_191203_1 random_191203_1_r
python -m pokeai.ai.rating_battle random_191203_1_r
```
`=> rate id: 5dee4bb7da9445dc2e5a60d0`

レート対戦
```
python -m pokeai.ai.rating_battle random_191203_1_r,acer_191209_13,hillclimb_191203_100_10_r --fixed_rate5dee4bb7da9445dc2e5a60d0 
```
`=> rate id: 5deee9acec3222fbe525670f`

エージェントタグ（生成条件）ごとのレートの平均を算出するpythonコードの例
```python
from pokeai.ai.party_db import col_party, col_agent, col_rate, pack_obj, unpack_obj, AgentDoc
from bson import ObjectId
import numpy as np
from pokeai.util import json_load

rate_id = ObjectId("5deee9acec3222fbe525670f")

entries = list(col_rate.aggregate([{"$match": {"_id": rate_id}},
                                      {"$project": {"rates": {"$objectToArray": "$rates"}}},
                                      {"$unwind": "$rates"},
                                      {"$project": {"rate": "$rates.v", "agent_id": {"$toObjectId": "$rates.k"}}},
                                      {"$lookup": {"from": "Agent", "localField": "agent_id",
                                                   "foreignField": "_id", "as": "agent"}},
                                      {"$unwind": "$agent"},
                                      {"$project": {"rate": 1, "agent_tags": "$agent.tags", "agent_id": "$agent._id", "party_id": "$agent.party_id"}},
                                      {"$lookup": {"from": "Party", "localField": "party_id",
                                                   "foreignField": "_id", "as": "party"}},
                                      {"$unwind": "$party"},
                                      {"$project": {"rate": 1, "agent_tags": 1, "agent_id": 1, "party_id": "$party._id", "party": "$party.party"}}]))

agent_tag_set = set()
for ent in entries:
    for t in ent["agent_tags"]:
        agent_tag_set.add(t)

for t in agent_tag_set:
    rates = []
    for ent in entries:
        if t in ent["agent_tags"]:
            rates.append(ent["rate"])
    print(t, np.mean(rates))
```

結果例
```
random_191203_1_r 1500.0000000000002
acer_191209_13 1884.946676770433
hillclimb_191203_100_10_r 1743.0361605228695
```

行動の定性評価をするにはバトルログの出力が必要。実行例:
```
python -m pokeai.ai.rating_battle acer_191209_13 --loglevel DEBUG > data/tmp/acer_191209_13_rating.log 2>&1
```
数百MBの長大なログが出てくるので、適宜フィルタリング＆目視でバトルの結果を追う。

# リトルカップ

```
python -m pokeai.ai.generate_party lc_random_191209_1 -n 10000 -r littlecup
python -m pokeai.ai.assign_random_policy lc_random_191209_1 lc_random_191209_1_r
python -m pokeai.ai.rating_battle lc_random_191209_1_r
rate_id: 5ded17d60813147901bac4da
python -m pokeai.ai.party_feature.train_party_rate_predictor data/ai/pr/prp_config_1.yaml 5ded17d60813147901bac4da data/ai/pr/lr_prp_1_cv --crossval 5
python -m pokeai.ai.party_feature.hillclimb_party data/ai/pr/lr_prp_1_cv/party_rate_predictor.bin lc_random_191209_2 lc_hillclimb_191209_100_100 --generations 100 --populations 100 -r littlecup
```
