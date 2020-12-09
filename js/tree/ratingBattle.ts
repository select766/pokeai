

import { AIBase } from "./aiBase";
import { ais } from "./ais";
import { argsort, rnorm } from "./mathUtil";
import { playout } from "./playout";
import { Sim } from "./sim";
import { loadJSON, saveJSON } from "./util";

interface Player {
    id: string;
    agent: AIBase;
    party: any;
}

interface AgentConfig {
    id: string;
    className: string;
    options: any;
}

function ratingBattle(players: Player[], matchCount: number): number[] {
    const rates: number[] = (new Array(players.length)).fill(1500);

    for (let i = 0; i < matchCount; i++) {
        console.log(`${new Date()}:${i}/${matchCount}`);
        const ratesWithRandom = rates.map((r) => r + rnorm() * 200);
        const ranking = argsort(ratesWithRandom);
        for (let j = 0; j < players.length; j += 2) {
            const left = ranking[j];
            const right = ranking[j + 1];
            const sim = Sim.fromParty([players[left].party, players[right].party]);
            const { winner } = playout(sim, [players[left].agent, players[right].agent]);
            if (winner) {
                const left_winrate = 1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0));
                let left_incr;
                if (winner === 'p1') {
                    left_incr = 32 * (1.0 - left_winrate);
                } else {
                    left_incr = 32 * (-left_winrate);
                }
                rates[left] += left_incr;
                rates[right] -= left_incr;
            }
        }
    }

    return rates;
}


function constructAgent(agentConfig: AgentConfig): AIBase {
    const ctor = ais[agentConfig.className];
    return new ctor(agentConfig.options);
}

function main() {
    const parties: { _id: string, party: any }[] = loadJSON(process.argv[2]);
    const agentConfigs: AgentConfig[] = loadJSON(process.argv[3]);
    const players: Player[] = [];
    for (const agentConfig of agentConfigs) {
        const agent = constructAgent(agentConfig);
        for (const party of parties) {
            players.push({ id: `${agentConfig.id}+${party._id}`, agent, party: party.party });
        }
    }

    console.time('all battles');
    const ratings = ratingBattle(players, 10);
    console.timeEnd('all battles');
    const results: { id: string; rate: number }[] = [];
    for (let i = 0; i < players.length; i++) {
        results.push({ id: players[i].id, rate: ratings[i] });
    }
    saveJSON(process.argv[4], results);
}

main();
