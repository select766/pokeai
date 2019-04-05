# 第2巻（初代3vs3編）：2019年4月（技術書典6）で刊行の本での実験の再現コマンド

開発を進めながら実験をしているため、もしかしたら同じ結果が得られないかもしれない。

# 環境構築
パーティ・エージェント等の一括管理のためにmongodbが必要なので、セットアップする。
実験当時のバージョン4.0.6。

環境変数(Windows用表記)を以下のように設定した状態で実験プログラムを動作させている。
```bat
set POKEAI_PARTY_DB_NAME=pokeai_1
set POKEAI_RULE_BLIZZARD_FREEZE_RATE=10
set MKL_NUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
set OMP_NUM_THREADS=1
```

- `POKEAI_PARTY_DB_NAME`: mongodb上のデータベース名。
- `POKEAI_RULE_BLIZZARD_FREEZE_RATE`: 「ふぶき」の追加効果発動確率(%)。10または30を設定する。
- `*_NUM_THREADS`: numpyでの行列計算をシングルスレッドで行う。設定しなくとも計算結果は同じ。

さかさバトルを行う場合、以下を追加。
```bat
set POKEAI_SAKASA=1
```

# パーティ評価関数の学習
```
# ランダムなパーティを生成
python -m pokeai.agent.make_random_pool 10000 --rule LVSUM155_3 --tag random_for_party_eval
python -m pokeai.agent.make_random_pool 10000 --rule LVSUM155_3 --tag random_for_benchmark
# パーティに対し、ランダムに行動するエージェントを付与
python -m pokeai.agent.assign_random_agent random_for_party_eval agent_random_random_for_party_eval
python -m pokeai.agent.assign_random_agent random_for_benchmark agent_random_random_for_benchmark
# 相互対戦してレーティング
python -m pokeai.agent.rating_battle agent_random_random_for_party_eval
# => rate id 5c680eb752338e7f903c0e72
python -m pokeai.agent.rating_battle agent_random_random_for_benchmark
# => rate id 5c6d3c6252338e9f7cfc8023
```

tagは同じ条件で生成されたパーティを総称する名前。

rating_battleによりエージェントが相互対戦しレートが割り振られる。レート情報にはランダムなidが付与され保存される。

```
python -m pokeai.agent.party_feature.train_party_rate_predictor rate_predictor\pm_1\config.yaml 5c680eb752338e7f903c0e72 rate_predictor\pm_1
```

`rate_predictor\pm_1\party_rate_predictor.bin`にモデルが保存される。

`config.yaml`の変更により特徴量の増減・学習パラメータの変更ができる。

# パーティの生成
```
python -m pokeai.agent.hill_climbing hill_climbing\hc_pred_1.yaml hc_pred_1 -j 3
```

`-j 3`は並列処理数。指定しなくともよい。

`hc_pred_1`の部分が設定ごとに異なる。

```
(A) 山登り法(10,10) hc_1
(B) 最良優先(10,100,10) hc_pred_1
(C) 評価関数のみ(100,10) hc_pred_only_1
(D) 評価関数のみ(100,1000) hc_pred_only_2
(E) 評価関数のみ(10,10) hc_pred_only_3
```

生成結果のレーティング
```
python -m pokeai.agent.assign_random_agent hc_1 agent_random_hc_1
# hc_1のほか、hc_pred_1などでも同様にassign_random_agentを行う
python -m pokeai.agent.rating_battle --fixed_rate 5c6d3c6252338e9f7cfc8023 agent_random_random_for_benchmark,agent_random_hc_1,agent_random_hc_pred_1,agent_random_hc_pred_only_1,agent_random_hc_pred_only_2,agent_random_hc_pred_only_3
# => rate id 5c727db452338e2ab1ea0124
```

`--fixed_rate 5c6d3c6252338e9f7cfc8023`は、既に測定されたレートを指定。これに含まれるエージェントは対戦結果によるレート変更を行わない。
ベンチマーク用のエージェントのレートを固定することで、環境に入れるエージェントの全体的な強弱による測定結果変動を回避することを目指している。

# 強化学習
行動を学習するパーティ群として、（ランダム行動下で最強の）hc_pred_only_2と、ランダム生成されたrandom_for_party_eval_s100を用いる。

ランダム生成のほうは、random_for_party_evalからランダムに100パーティ選択する。jupyterで以下を実行。
```python
from bson import ObjectId
from pokeai.agent import party_db
import numpy as np
import pickle
import random

def make_subset(src_tag, size, tag):
    dst_group_id = ObjectId()
    all_ids = party_db.col_party_group.find_one({"tags": src_tag})["party_ids"]
    subset_ids = random.sample(all_ids, k=size)
    party_db.col_party_group.insert_one({
        "_id": dst_group_id,
        "party_ids": subset_ids,
        "tags": [str(dst_group_id), tag]
    })
    print(dst_group_id)

make_subset("random_for_party_eval", 100, "random_for_party_eval_s100")
```

条件を変えてエージェントを学習。全部やると数日かかる。出力されるエージェントのtagはagent_rl_20190301_0等。
```
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_0 agent_rl_20190301_0 random_for_party_eval_s100 agent_random_random_for_party_eval agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_1 agent_rl_20190301_1 random_for_party_eval_s100 agent_random_random_for_party_eval agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_2 agent_rl_20190301_2 random_for_party_eval_s100 agent_random_random_for_party_eval agent_config/rl_20190301_r2.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_3 agent_rl_20190301_3 random_for_party_eval_s100 agent_random_hc_pred_only_2 agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_4 agent_rl_20190301_4 random_for_party_eval_s100 agent_random_hc_pred_only_2 agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_5 agent_rl_20190301_5 random_for_party_eval_s100 agent_random_hc_pred_only_2 agent_config/rl_20190301_r2.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_6 agent_rl_20190301_6 hc_pred_only_2 agent_random_random_for_party_eval agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_7 agent_rl_20190301_7 hc_pred_only_2 agent_random_random_for_party_eval agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_8 agent_rl_20190301_8 hc_pred_only_2 agent_random_random_for_party_eval agent_config/rl_20190301_r2.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_9 agent_rl_20190301_9 hc_pred_only_2 agent_random_hc_pred_only_2 agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_10 agent_rl_20190301_10 hc_pred_only_2 agent_random_hc_pred_only_2 agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_11 agent_rl_20190301_11 hc_pred_only_2 agent_random_hc_pred_only_2 agent_config/rl_20190301_r2.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_12 agent_rl_20190301_12 random_for_party_eval_s100 agent_rl_20190301_9 agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_13 agent_rl_20190301_13 random_for_party_eval_s100 agent_rl_20190301_9 agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_14 agent_rl_20190301_14 random_for_party_eval_s100 agent_rl_20190301_9 agent_config/rl_20190301_r2.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_15 agent_rl_20190301_15 hc_pred_only_2 agent_rl_20190301_9 agent_config/rl_20190301_r0.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_16 agent_rl_20190301_16 hc_pred_only_2 agent_rl_20190301_9 agent_config/rl_20190301_r1.yaml
python -m pokeai.agent.train_battle_policy rl_agents/rl_20190301_17 agent_rl_20190301_17 hc_pred_only_2 agent_rl_20190301_9 agent_config/rl_20190301_r2.yaml
```

引数
- エージェントのモデルファイル出力ディレクトリ
- エージェントtag
- パーティ
- 敵エージェントtag
- 学習パラメータファイル（特徴量、モデル構造、学習率、報酬等）

比較用レーティングバトル
```
python -m pokeai.agent.rating_battle --fixed_rate 5c6d3c6252338e9f7cfc8023 agent_random_random_for_benchmark,agent_rl_20190301_0,agent_rl_20190301_1,agent_rl_20190301_2,agent_rl_20190301_3,agent_rl_20190301_4,agent_rl_20190301_5,agent_rl_20190301_6,agent_rl_20190301_7,agent_rl_20190301_8,agent_rl_20190301_9,agent_rl_20190301_10,agent_rl_20190301_11,agent_rl_20190301_12,agent_rl_20190301_13,agent_rl_20190301_14,agent_rl_20190301_15,agent_rl_20190301_16,agent_rl_20190301_17
# => rate id 5c7d13f252338ea2f436d96f
```

結果（参考）
|agent_tag|条件|mean rate|
|---|---|---|
|agent_random_random_for_benchmark||1500|
|agent_rl_20190301_0|partyg=random_for_party_eval_s100,enemy=agent_random_random_for_party_eval,reward=0|1768.384797|
|agent_rl_20190301_1|partyg=random_for_party_eval_s100,enemy=agent_random_random_for_party_eval,reward=1|1761.628308|
|agent_rl_20190301_102|partyg=random_for_party_eval_s100,enemy=agent_random_random_for_party_eval,reward=2|1756.260562|
|agent_rl_20190301_3|partyg=random_for_party_eval_s100,enemy=agent_random_hc_pred_only_2,reward=0|1661.929375|
|agent_rl_20190301_4|partyg=random_for_party_eval_s100,enemy=agent_random_hc_pred_only_2,reward=1|1556.471813|
|agent_rl_20190301_105|partyg=random_for_party_eval_s100,enemy=agent_random_hc_pred_only_2,reward=2|1616.731193|
|agent_rl_20190301_6|partyg=hc_pred_only_2,enemy=agent_random_random_for_party_eval,reward=0|2044.086652|
|agent_rl_20190301_7|partyg=hc_pred_only_2,enemy=agent_random_random_for_party_eval,reward=1|2034.679443|
|agent_rl_20190301_108|partyg=hc_pred_only_2,enemy=agent_random_random_for_party_eval,reward=2|2032.31838|
|agent_rl_20190301_9|partyg=hc_pred_only_2,enemy=agent_random_hc_pred_only_2,reward=0|2073.601892|
|agent_rl_20190301_10|partyg=hc_pred_only_2,enemy=agent_random_hc_pred_only_2,reward=1|2078.76443|
|agent_rl_20190301_111|partyg=hc_pred_only_2,enemy=agent_random_hc_pred_only_2,reward=2|2068.728535|
|agent_rl_20190301_112|partyg=random_for_party_eval_s100,enemy=agent_rl_20190301_9,reward=0|1573.857683|
|agent_rl_20190301_113|partyg=random_for_party_eval_s100,enemy=agent_rl_20190301_9,reward=1|1451.215852|
|agent_rl_20190301_114|partyg=random_for_party_eval_s100,enemy=agent_rl_20190301_9,reward=2|1507.567613|
|agent_rl_20190301_115|partyg=hc_pred_only_2,enemy=agent_rl_20190301_9,reward=0|2107.552692|
|agent_rl_20190301_116|partyg=hc_pred_only_2,enemy=agent_rl_20190301_9,reward=1|2060.830425|
|agent_rl_20190301_117|partyg=hc_pred_only_2,enemy=agent_rl_20190301_9,reward=2|2082.511187|

エージェントtagごとの平均レート計算コード例
```python
from bson import ObjectId
from pokeai.agent import party_db
import numpy as np
import pickle

def get_rate_agent_tag_parties(rate_id):
    rates = []
    agent_tags = []
    parties = []
    agent_ids = []
    for record in party_db.col_rate.aggregate([{"$match":{"_id":rate_id}},
{"$unwind": "$rates"},
{"$project": {"rate": "$rates.rate", "agent_id": "$rates.agent_id"}},
{"$lookup": {"from":"Agent","localField":"agent_id","foreignField":"_id","as":"agent"}},
{"$unwind": "$agent"},
{"$project": {"rate": 1, "agent_id": 1, "agent_tags": "$agent.tags", "party_id": "$agent.party_id"}},
{"$lookup": {"from": "Party", "localField":"party_id", "foreignField":"_id","as":"party"}},
{"$unwind": "$party"}
]):
        #  { "_id" : ObjectId("5c6182bc52338e024b4ef580"), "rate" : 1727.2075623827332, "party_id" : ObjectId("5c6165f452338e9c588ee3b8"), "party" : { "_id" : ObjectId("5c6165f452338e9c588ee3b8"), "party_template" : BinData(0,"...") } }
        rates.append(record["rate"])
        agent_ids.append(record["agent_id"])
        agent_tags.append(record["agent_tags"])
        parties.append(pickle.loads(record["party"]["party_template"]))
    return rates, agent_tags, parties, agent_ids

rates, agent_tags, parties, agent_ids = get_rate_agent_tag_parties(ObjectId("5c7d13f252338ea2f436d96f"))

def filter_parties_rates(rates, parties, agent_tags, agent_tag, agent_ids):
    retrates = []
    retparties = []
    retagent_ids = []
    for i in range(len(rates)):
        if agent_tag in agent_tags[i]:
            retrates.append(rates[i])
            retparties.append(parties[i])
            retagent_ids.append(agent_ids[i])
    return retrates, retparties, retagent_ids

atags = "agent_random_random_for_benchmark,agent_rl_20190301_0,agent_rl_20190301_1,agent_rl_20190301_2,agent_rl_20190301_3,agent_rl_20190301_4,agent_rl_20190301_5,agent_rl_20190301_6,agent_rl_20190301_7,agent_rl_20190301_8,agent_rl_20190301_9,agent_rl_20190301_10,agent_rl_20190301_11,agent_rl_20190301_12,agent_rl_20190301_13,agent_rl_20190301_14,agent_rl_20190301_15,agent_rl_20190301_16,agent_rl_20190301_17".split(",")

for atag in atags:
    frates, fparties, _ = filter_parties_rates(rates, parties, agent_tags, atag, agent_ids)
    print(f"{atag}: size={len(frates)} mean rate={np.mean(frates)}")
```
