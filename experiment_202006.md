# 汎用行動選択モデルの教師あり学習と強化学習の比較

2020年6月時点。

2020年3月まではパーティと、パーティ1つに対応するエージェントを保存していたが、エージェントが任意のパーティに対応するようになったため、学習したモデルはTrainerという名前で保存するように変更した。mongodbのDB名を`pokeai_2`から`pokeai_3`に変更している。

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
