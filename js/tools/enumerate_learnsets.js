/*
  ポケモンが覚える可能性のある技を列挙
  進化前限定技も含む。
  覚える条件は考慮しない。複数の技が特定レベルで両立可能かは別途判定。

  node ./js/tools/enumerate_learnsets.js > data/dataset/all_learnsets.json

  出力イメージ
  {
    "bulbasaur": [
        "ancientpower",
        "attract",
        "bide",
        "bodyslam",
*/

const sim = require('../../Pokemon-Showdown/.sim-dist');
const mdex = new sim.Dex.ModdedDex('gen1');
const pokemons = require('../../data/dataset/all_pokemons.json');

// 進化前限定も含めて覚える技の列挙
const get_learnset = (pokemon) => {
    let tmpl = mdex.getTemplate(pokemon);
    const learnset = new Set();
    // 第2世代の技が入っている。
    // 覚える条件の文字列先頭が"2"となっているものが第2世代で覚えるということなので、第1世代で覚えるもののみに限定
    // 「タイムカプセル」で金銀で育成したポケモンを初代に送るなら、初代に存在するが金銀でだけ覚えられるものを入れることも考慮して変更すること
    //       "growth": [
    //    "1L34",
    //    "2L32"
    //  ],
    for (const move in tmpl.learnset) {
        const conditions = tmpl.learnset[move]; // ["1L34", "2L32"]
        if (conditions.some((c) => c.startsWith("1"))) {
            learnset.add(move);
        }
    }
    const prevo = tmpl.prevo;
    if (prevo && pokemons.includes(prevo)) {//進化前のポケモンID
        // 進化前が現行世代に存在しなくてもtmpl.prevoに入っているので注意。pokemons.includeでチェック。
        const prevo_learnset = get_learnset(prevo);
        prevo_learnset.forEach(move => learnset.add(move));
    }

    // アルファベット順にソート
    const learnset_array = [...learnset];
    learnset_array.sort();

    return learnset_array;
};

const all_learnset = {};
pokemons.forEach(poke => { all_learnset[poke] = get_learnset(poke); });
process.stdout.write(JSON.stringify(all_learnset, null, 2));
