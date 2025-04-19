
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

パーティ勝敗データセット作成

```bash
python -m pokeai.ai.selection.generate_party_match_dataset data/party_match_dataset_train_n1m_m1.jsonl -r finalgoodmove1vs1 -m 1 -n 1000000
python -m pokeai.ai.selection.generate_party_match_dataset data/party_match_dataset_val_n1k_m100.jsonl -r finalgoodmove1vs1 -m 100 -n 1000
python -m pokeai.ai.selection.generate_party_match_dataset data/party_match_dataset_test_n1k_m100.jsonl -r finalgoodmove1vs1 -m 100 -n 1000
# 特徴量の準備
python -m pokeai.ai.selection.party_match_dataset_feat_prepare -r finalgoodmove1vs1 data/party_match_feat_mapping_finalgoodmove1vs1.json
for f in data/party_match_dataset_*.jsonl; do python party_match_dataset_feat.py ${f%.*}.pth $f data/party_match_feat_mapping_finalgoodmove1vs1.json ; done

# 学習
python -m pokeai.ai.selection.party_match_train data/party_match_dataset_train_n1m_m1.pth data/party_match_dataset_val_n1k_m100.pth data/train1 --feat_map data/party_match_feat_mapping_finalgoodmove1vs1.json

PYTHONUNBUFFERED=1 python -m pokeai.ai.selection.do_loop_baseline data/do_loop_baseline_02.pkl -r finalgoodmove3vs3lv55all --feat_map data/party_match_feat_mapping_finalgoodmove1vs1.json --model data/train1/model_final.pth --hill_climb_iterations 100 --neighbor_iterations 100 --num_cycles 100 | tee -a data/do_loop_baseline_02.log
```


```bash
python -m pokeai.ai.selection.generate_party_match_dataset data/party_match_dataset_final1vs1_mcv_val_n1k_m100.jsonl -r final1vs1 --move_count_variation -m 100 -n 1000 &
python -m pokeai.ai.selection.generate_party_match_dataset data/party_match_dataset_final1vs1_mcv_test_n1k_m100.jsonl -r final1vs1 --move_count_variation -m 100 -n 1000 &
for i in {0..9}; do
  python -m pokeai.ai.selection.generate_party_match_dataset data/tmp_party_match_dataset_final1vs1_mcv_train_n1m_m1_split${i}.jsonl -r final1vs1 --move_count_variation -m 1 -n 1000000 &
done
wait

cat data/tmp_party_match_dataset_final1vs1_mcv_train_n1m_m1_split*.jsonl > data/party_match_dataset_final1vs1_mcv_train_n10m_m1.jsonl

python -m pokeai.ai.selection.party_match_dataset_feat_prepare -r final1vs1 data/party_match_feat_mapping_final1vs1.json
for f in data/party_match_dataset_final1vs1*.jsonl; do python -m pokeai.ai.selection.party_match_dataset_feat ${f%.*}.pth $f data/party_match_feat_mapping_final1vs1.json ; done
python -m pokeai.ai.selection.party_match_train_optuna data/party_match_dataset_final1vs1_mcv_train_n10m_m1.pth data/party_match_dataset_final1vs1_mcv_val_n1k_m100.pth data/train_final1vs1_mcv_1 --feat_map data/party_match_feat_mapping_final1vs1.json --n_trials 100 --optuna_storage sqlite:///data/optuna.db --optuna_study_name "final1vs1_mcv_1" | tee data/train_final1vs1_mcv_1.log

PYTHONUNBUFFERED=1 python -m pokeai.ai.selection.do_loop_baseline data/do_loop_baseline_final1vs1_mcv_01.pkl -r final3vs3lv55all --feat_map data/party_match_feat_mapping_final1vs1.json --model data/train_final1vs1_mcv_1/best_model.pth --hill_climb_iterations 100 --neighbor_iterations 100 --num_cycles 100 --move_count_variation | tee -a data/do_loop_baseline_final1vs1_mcv_01.log
```
