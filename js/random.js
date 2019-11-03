const bs = require('../Pokemon-Showdown/.sim-dist/battle-stream');
const BattleStream = bs.BattleStream;
const getPlayerStreams = bs.getPlayerStreams;
const dex = require('../Pokemon-Showdown/.sim-dist/dex');
const Dex = dex.Dex;
const randomplayerai = require('../Pokemon-Showdown/.sim-dist/tools/random-player-ai');
const RandomPlayerAI = randomplayerai.RandomPlayerAI;

const randomBattle = () => {
    return new Promise((resolve) => {
        const streams = getPlayerStreams(new BattleStream());

        const spec = {
            formatid: "gen2customgame",
        };
        const parties = [];
        const partyspecs = [];
        for (let i = 0; i < 2; i++) {

            const party = Dex.generateTeam('gen2customgame').slice(0, 3);
            const partyspec = {
                name: '' + i,
                team: Dex.packTeam(party),
            };

            const player = new RandomPlayerAI(streams[['p1', 'p2'][i]]);
            player.start();
            parties.push(party);
            partyspecs.push(partyspec);
        }

        (async () => {
            let chunk;
            let end = false;
            while (!end && (chunk = await streams.omniscient.read())) {
                for (const line of chunk.split('\n')) {
                    if (line.startsWith('|win|')) {
                        // |win|0 or |win|1
                        const winner = Number(line.slice(5));
                        end = true;
                        resolve({ parties, winner });
                        break;
                    }
                    if (line.startsWith('|turn|')) {
                        // |turn|100
                        const turn = Number(line.slice(6));
                        if (turn >= 64) {
                            end = true;
                            resolve({ parties, winner: -1 });
                        }
                        break;
                    }
                }
            }
        })();

        streams.omniscient.write(`>start ${JSON.stringify(spec)}
>player p1 ${JSON.stringify(partyspecs[0])}
>player p2 ${JSON.stringify(partyspecs[1])}`);
    });
}

(async () => {
    for (let i = 0; i < 100000; i++) {
        const battle_result = await randomBattle();
        console.log(JSON.stringify(battle_result));
    }
})();

