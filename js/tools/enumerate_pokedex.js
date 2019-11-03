/*
  ポケモンの基本情報の列挙
  タイプ、性別比率などをパーティ生成に利用する
  node ./js/tools/enumerate_pokedex.js > data/dataset/pokedex.json
*/

const sim = require('../../Pokemon-Showdown/.sim-dist');
const mdex = new sim.Dex.ModdedDex('gen2');
const pokemons = require('../../data/dataset/all_pokemons.json');

const dex = {};
pokemons.forEach(poke => {
    dex[poke] = mdex.getTemplate(poke);
});
process.stdout.write(JSON.stringify(dex, null, 2));
