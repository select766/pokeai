// 標準入出力によるプロセス間通信によりシミュレータを公開
// chunk単位をjsonシリアライズして1行で送受信

const bs = require('../Pokemon-Showdown/.sim-dist/battle-stream');
const BattleStream = bs.BattleStream;

const stream = new BattleStream();

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
