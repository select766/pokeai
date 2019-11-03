// パーティ構成が有効が有効かを判定する
// 技の組み合わせが正しいか
// jsonシリアライズして送受信

const sim = require('../Pokemon-Showdown/.sim-dist');
const mdex = new sim.Dex.ModdedDex('gen2');
const tv = new sim.TeamValidator('gen2customgame');
tv.ruleTable.set('-illegal','')//覚えられない技の検証を行う設定

var reader = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
});
reader.on('line', function (line) {
    /*
    party:
    [ { name: 'Moltres',//ファイヤー
    species: 'Moltres',
    moves: [ 'Leer' ],//にらみつける(LV51で覚える)
    ability: 'No Ability',
    evs:
     { hp: 255, atk: 255, def: 255, spa: 255, spd: 255, spe: 255 },
    ivs: { hp: 30, atk: 30, def: 30, spa: 30, spd: 30, spe: 30 },
    item: 'Leftovers',
    level: 51,
    shiny: false,
    gender: 'M',
    nature: '' },
    , <2番目以降のポケモン> ]
    */
    const party = JSON.parse(line);
    /* result:
    パーティが有効ならnull
    無効なら理由を列挙したstring[]
    [ 'Moltres can\'t learn Leer.' ] (LV50のファイヤーの例)
    */

    const result = tv.validateTeam(party);
    process.stdout.write(JSON.stringify(result) + '\n');
});
