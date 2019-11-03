/*
  存在する技の列挙
  all_learnsets.jsonから技を抽出する
  + "struggle"(わるあがき)

  node ./js/tools/enumerate_moves.js > data/dataset/all_moves.json

  data/modes/gen2/moves.jsは他世代と仕様の違う技しか書いてない
*/

const all_learnsets = require('../../data/dataset/all_learnsets.json');

const moves = new Set();
for (const poke_moves of Object.values(all_learnsets)) {
    poke_moves.forEach(m => moves.add(m));
}

const sorted_moves = [...moves, 'struggle'];
sorted_moves.sort();

process.stdout.write(JSON.stringify(sorted_moves, null, 2));
