// 標準入出力によるプロセス間通信によりシミュレータを公開
// chunk単位をjsonシリアライズして1行で送受信

const bs = require('../Pokemon-Showdown/dist/sim/battle-stream');
const BattleStream = bs.BattleStream;

// keepAlive: 複数回バトルを行えるようにする(デフォルトではバトルが終了するとストリームが閉じられる)
const stream = new BattleStream({ debug: false, keepAlive: true });

const reader = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
});
reader.on('line', function (line) {
    stream.write(JSON.parse(line));
});

(async () => {
    let chunk;
    while (chunk = await stream.read()) {
        process.stdout.write(JSON.stringify(chunk) + '\n');
    }
})();
