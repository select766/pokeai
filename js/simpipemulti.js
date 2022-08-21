// 標準入出力によるプロセス間通信によりシミュレータを公開
// chunk単位をjsonシリアライズして1行で送受信
// 複数のシミュレータを１プロセスで動かせる

const bs = require('../Pokemon-Showdown/.sim-dist/battle-stream');
const BattleStream = bs.BattleStream;


const streams = new Map(); // Map<string, BattleStream>
const reader = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout
});

function createStream(id) {
    // keepAlive: 複数回バトルを行えるようにする(デフォルトではバトルが終了するとストリームが閉じられる)
    const stream = new BattleStream({ debug: false, keepAlive: true });
    (async () => {
        let chunk;
        while (chunk = await stream.read()) {
            process.stdout.write(JSON.stringify({chunk, id, type: 'read'}) + '\n');
        }
        // stream.end()を呼ぶと、stream.read()がnullを返すはず
    })();
    return stream;
}

reader.on('line', function (line) {
    const message = JSON.parse(line);
    switch (message.type) {
        case 'open':
            // {type: 'open', id: string}
            streams.set(message.id, createStream(message.id));
            break;
        case 'write':
            // {type: 'write': id: string, chunk: any}
            streams.get(message.id)?.write(message.chunk);
            break;
        case 'close':
            // {type: 'close': id: string}
            streams.get(message.id)?.end();
            streams.delete(message.id);
    }
});

