# 第1巻（初代1vs1編）：2018年10月（技術書典5）で刊行の本での実験の再現コマンド

実際の実行結果を分析したjupyter notebookは[releases](https://github.com/select766/pokeai/releases)で配布。

# 実験1: 山登り法
```
# グループAの生成
python -m pokeai.agent.make_random_pool group_a.bin 1000
python -m pokeai.agent.rate_random_policy group_a_rate.bin group_a.bin
# グループXの生成
python -m pokeai.agent.make_random_pool group_x.bin 1000
python -m pokeai.agent.rate_random_policy group_x_rate.bin group_x.bin
# グループB,C,Yシードの生成
python -m pokeai.agent.make_random_pool group_b_seed.bin 1000
python -m pokeai.agent.make_random_pool group_c_seed.bin 1000
python -m pokeai.agent.make_random_pool group_y_seed.bin 1000
# パーティBの最適化
python -m pokeai.agent.hill_climbing group_b.bin group_b_seed.bin group_x.bin group_x_rate.bin  --rule_params rule_params.yaml --neighbor 10 --iter  30 --history -j 3
python -m pokeai.agent.rate_random_policy group_b_rate.bin group_b.bin
# グループYの最適化
python -m pokeai.agent.hill_climbing group_y.bin group_y_seed.bin group_x.bin group_x_rate.bin  --rule_params rule_params.yaml --neighbor 10 --iter  30 --history -j 3
python -m pokeai.agent.rate_random_policy group_y_rate.bin group_y.bin
# グループCの最適化
python -m pokeai.agent.hill_climbing group_c.bin group_c_seed.bin group_y.bin group_y_rate.bin  --rule_params rule_params.yaml --neighbor 10 --iter  30 --history -j 3
python -m pokeai.agent.rate_random_policy group_c_rate.bin group_c.bin
# 各パーティの上位を選択
python -m pokeai.agent.filter_party group_a_top group_a --count 20
python -m pokeai.agent.filter_party group_b_top group_b --count 20
python -m pokeai.agent.filter_party group_c_top group_c --count 20
# レーティング
python -m pokeai.agent.rate_random_policy group_abc_top_rate.bin group_a_top.bin group_b_top.bin group_c_top.bin
```

# 実験2: 強化学習
```
# グループDの行動学習
python -m pokeai.agent.hill_climbing_rl group_d group_b_top.bin group_x.bin group_x_rate.bin --iter 0 -j 3
# グループEの行動学習
python -m pokeai.agent.hill_climbing_rl group_e group_b_top.bin group_y.bin group_y_rate.bin --iter 0 -j 3
# レーティング
python -m pokeai.agent.rate_rl_policy rate.bin group_b_top.bin group_d/parties.bin group_e/parties.bin
```

# 実験3: 交互最適化
```
# グループZ作成
python -m pokeai.agent.make_random_pool group_z_seed.bin 1000
python -m pokeai.agent.hill_climbing group_z.bin group_z_seed.bin group_x.bin group_x_rate.bin  --rule_params rule_params.yaml --neighbor 10 --iter  30 --history -j 3
python -m pokeai.agent.rate_random_policy group_z_rate.bin group_z.bin
python -m pokeai.agent.filter_party group_z_top group_z --count 20
# グループF作成
python -m pokeai.agent.hill_climbing_rl group_f group_z_top.bin group_y.bin group_y_rate.bin --neighbor 10 --iter 30 -j 3
# グループZの行動学習=H
python -m pokeai.agent.hill_climbing_rl group_h group_z_top.bin group_y.bin group_y_rate.bin --iter 0 -j 3
# グループE,F,Hの対戦レーティング
python -m pokeai.agent.rate_rl_policy rate.bin group_e/parties.bin group_f/parties.bin group_h/parties.bin
```
