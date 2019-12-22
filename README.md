# PokéAI ～人工知能の考えた最強のポケモン対戦戦略～
PokéAI(ポケエーアイ)は、ポケモンバトルの戦略を人工知能に考えさせ、
究極的には人が思いつかなかったような戦略を編み出すことを目標とするプロジェクトです。

シミュレータとして[Pokémon Showdown](https://github.com/Zarel/Pokemon-Showdown)を利用。

初代ルールのシミュレータ実装とAI -> [book-201904](https://github.com/select766/pokeai/tree/book-201904)

成果は同人誌の形で発表。頒布情報は[blog](http://select766.hatenablog.com/archive/category/%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3)参照。

# setup
node v10.x が必要。

```
git submodule update -i
cd Pokemon-Showdown
npm run build
```

python 3.8が必要。

```
pip install -r requirements.txt
python3 setup.py develop
```

mongodb 4.xが必要。コードを実行することで、デフォルトでは`pokeai_2`データベースを生成する。

# 基本構成

* `/js`: シミュレータを直接呼び出すJavaScriptコード
* `/pokeai`: Pythonコード
  * `/sim`: シミュレータとPython環境の橋渡し
  * `/ai`: AI機能
* `/data`: ポケモンリスト、対戦ルール等

# 実験方法
masterブランチは随時更新されるため、過去の実験コマンドが動かなくなっている場合があります。過去のバージョンは[tags](https://github.com/select766/pokeai/tags)から参照ください。

- 第3巻（金銀導入編）：2019年12月（コミックマーケット97）で刊行の本での実験の再現コマンド→[experiment_201912.md](experiment_201912.md)

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。
