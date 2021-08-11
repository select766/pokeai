/*
  ポケモン名（キー）の列挙
  node ./js/tools/enumerate_pokemons.js > data/dataset/all_pokemons.json
*/

const pokedex = require('../../Pokemon-Showdown/data/mods/gen1/pokedex');
// ['missingno', 'bulbasaur', 'ivysaur', ..., 'cerebi']
// 実装依存ではあるが図鑑番号順に並ぶ
// けつばんが入ってるので除外
const gen1pokes = Object.keys(pokedex.BattlePokedex).filter((name) => name !== "missingno");

process.stdout.write(JSON.stringify(gen1pokes, null, 2));