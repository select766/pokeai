
```bash
# ランダムパーティ生成
python -m pokeai.ai.generate_party random_20241106_1 -n 1000 -r finalgoodmove1vs1
# それらを対戦させてレートをつける
python -m pokeai.ai.generic_move_model.rl_rating_battle "#random" random_20241106_1 --rate_id 672b539e2fb3394b4a0b8ed0
# レートの高いパーティを抽出
python export_top_rate_party.py 672b539e2fb3394b4a0b8ed0 "nash2024/data/random_top_100.json"
# レートの高いパーティを総当たりで対戦させる
python -m pokeai.ai.generic_move_model.rl_rating_battle "" "" --player_ids_file nash2024/data/random_top_100.json --match_count 9900 --match_algorithm round_robin --match_results_dir nash2024/data/ --rate_id 672b5e0f89c3cd9202fe28b4
```
