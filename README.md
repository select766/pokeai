# PokéAI
Develop ultimate AI Pokémon trainer

# コマンド

パーティ群生成
```
python -m pokeai.ai_v4.generate_random_pool data\parties\random_test_pool_100.pickle 100
```

パーティ相互対戦
```
python -m pokeai.ai_v4.party_match params\party_group_20171217.yaml params\hill_climbing_rl.yaml
```

事前生成したパーティ群（ランダム行動）との対戦
```
python -m pokeai.ai_v4.party_match params\party_group_20171217.yaml params\hill_climbing_rl.yaml --enemy_parties data\parties\random_test_pool_100.pickle
```
