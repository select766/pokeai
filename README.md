# PokéAI ～ポケモンバトルAIのつくりかた～
PokéAI(ポケエーアイ)は、ポケモンバトルの戦略を人工知能に考えさせ、
究極的には人が思いつかなかったような戦略を編み出すことを目標とするプロジェクトです。

成果は同人誌の形で発表。頒布情報は[HP](https://select766.github.io/)参照。2018年10月発行の第1巻はPDF無料配布中。

シミュレータとして[Pokémon Showdown](https://github.com/Zarel/Pokemon-Showdown)を利用。

初代ルールのシミュレータ実装とAI -> [book-201904](https://github.com/select766/pokeai/tree/book-201904)

# setup

**現在改修中で整合性が取れていません。過去のタグを利用してください。**

node v20.x が必要。

```
git submodule update -i
cd Pokemon-Showdown
npm run build
```

python 3.11+poetryが必要。

```
poetry install
```

mongodb 4.xが必要。コードを実行することで、デフォルトでは`pokeai_4`データベースを生成する。

`.env` ファイルを作成。

```
POKEAI_PARTY_DB_HOST=<mongodbが動作しているマシンのIPアドレス>
POKEAI_PARTY_DB_NAME=<mongodbのデータベース名(defaultは"pokeai_4")>
```

# 基本構成

* `/js`: シミュレータを直接呼び出すJavaScriptコード
* `/pokeai`: Pythonコード
  * `/sim`: シミュレータとPython環境の橋渡し
  * `/ai`: AI機能
* `/data`: ポケモンリスト、対戦ルール等

# 実験方法
本にした実験は`reproduce`ディレクトリに情報があります。masterブランチは随時更新されるため、過去の実験コマンドが動かなくなっている場合があります。過去のバージョンは[tags](https://github.com/select766/pokeai/tags)から参照ください。

# ライセンス
コードはMITライセンスとしております。本については、ファイル内のライセンス表記をご参照ください。
