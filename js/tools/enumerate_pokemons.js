/*
  ポケモン名（キー）の列挙
  node ./js/tools/enumerate_pokemons.js > data/dataset/all_pokemons.json
*/

const learnsets = require('../../Pokemon-Showdown/data/mods/gen2/learnsets');
process.stdout.write(JSON.stringify(Object.keys(learnsets.BattleLearnsets), null, 2));
// ['bulbasaur', 'ivysaur', ..., 'cerebi']
// 実装依存ではあるが図鑑番号順に並ぶ
