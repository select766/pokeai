# とりあえずランダムパーティのレート計算

```bash
python -m pokeai.ai.generate_party random_20240429_2 -n 2000 -r finalgoodmove1vs1
python -m pokeai.ai.generic_move_model.rl_rating_battle #random random_20240429_2
```
`rate_id: 662f7d37e3b2dde6cd5146a4`

# 対戦ログ保存

```bash
python -m pokeai.ai.generate_party random_20240429_1 -n 10000 -r finalgoodmove1vs1
python -m pokeai.ai.generic_move_model.rl_rating_battle #random random_20240429_1 --rate_id 662f68cad1f571f3ed82b775 --loglevel DEBUG --log rl_rating_battle_662f68cad1f571f3ed82b775.log --match_count 100
```

# 100パーティで1万回対戦

```bash
python -m pokeai.ai.generate_party random_20240430_1 -n 100 -r finalgoodmove1vs1
python -m pokeai.ai.generic_move_model.rl_rating_battle #random random_20240430_1 --rate_id 662f68cad1f571f3ed82b776 --loglevel DEBUG --log rl_rating_battle_662f68cad1f571f3ed82b776.log --match_count 10000
```
