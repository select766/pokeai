// パーティリストを読み込み、全組み合わせでランダムプレイアウトして勝率を計算する

import * as fs from "fs";

import { AIRandom } from "./aiRandom";
import { playout } from "./playout";
import { Sim } from "./sim";

function loadData(path: string): {_id: string, party: any}[] {
    return JSON.parse(fs.readFileSync(path, {encoding: 'utf-8'}));
}

function main() {
    const parties = loadData(process.argv[2]);
    const aiRandom = new AIRandom();
    const results = [];
    console.time('all battles');
    for (let i = 0; i < parties.length; i++) {
        console.log(`${i}/${parties.length}`);
        console.time('battles');
        for (let j = 0; j < 10; j++) {
            const ridx = Math.random() * parties.length | 0;
            const sim = Sim.fromParty([parties[i].party,parties[ridx].party]);
            const playoutResult = playout(sim, [aiRandom, aiRandom]);
            results.push({p1: parties[i]._id, p2: parties[ridx]._id, result: playoutResult});
        }
        console.timeEnd('battles');
    }
    console.timeEnd('all battles');
    fs.writeFileSync(process.argv[3], JSON.stringify(results));
}

main();
