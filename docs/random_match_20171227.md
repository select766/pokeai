強さ測定用敵パーティ生成
```
python -m pokeai.ai_v4.generate_random_pool party\random_20171227\random_pool_100.pickle 100
```

パーティランダム生成・強さ測定
```
python -m pokeai.ai_v4.hill_climbing params\random_match_20171227\hill_climbing_simple_random.yaml --trials 10000
```

これで、固定された敵パーティ群に対して、ランダムパーティの勝率が求まる。

`run/hill_climbing/*`に山登り法プログラムの結果として出力が得られる。

特徴量抽出

先ほどの出力ファイルを指定。
```
python -m pokeai.ai_v4.party_feature D:\dev\pokeai\work\run\hill_climbing\20171227225451_1156\trial_results.pickle
```
