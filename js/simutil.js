// シミュレータの付属機能を呼び出しpythonと仲介するユーティリティ
// jsonシリアライズして送受信

const sim = require('../Pokemon-Showdown/.sim-dist');
const Dex = sim.Dex;
const methods = {};

methods['validateTeam'] = (() => {
    const tv = new sim.TeamValidator('gen2customgame');
    tv.ruleTable.set('-illegal', '')//覚えられない技の検証を行う設定

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
    /* result:
    パーティが有効ならnull
    無効なら理由を列挙したstring[]
    [ 'Moltres can\'t learn Leer.' ] (LV50のファイヤーの例)
    */
    return async (params) => {
        return tv.validateTeam(params['party']);
    };
})();

const reader = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
});
reader.on('line', async function (line) {
    const request = JSON.parse(line);
    const method = methods[request['method']];
    let result = null;
    let error = null;
    if (method) {
        try {
            result = await method(request['params']);
        } catch (ex) {
            error = ex;
        }
    } else {
        error = { 'message': `No method named ${request['method']}` };
    }
    process.stdout.write(JSON.stringify({ result, error }) + '\n');
});
