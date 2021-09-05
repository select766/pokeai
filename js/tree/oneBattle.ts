// パーティを指定して1回だけバトルをし、ログを出力する

import * as fs from 'fs';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

import { AIBase } from "./aiBase";
import { ais } from "./ais";
import { BattleLog } from './battleLogModel';
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

function oneBattle(players: Player[], logFile?: number, logLevel?: number): void {
    const left = 0;
    const right = 1;
    const sim = Sim.fromParty([players[left].party, players[right].party]);
    const { winner, log } = playout(sim, [players[left].agent, players[right].agent], logLevel);
    if (logFile && log) {
        const entry: BattleLog = {
            agents: {
                'p1': { player_id: players[left].id, party: players[left].party },
                'p2': { player_id: players[right].id, party: players[right].party }
            },
            events: log,
            end: { winner: winner || '' }
        };
        fs.writeSync(logFile, JSON.stringify(entry) + '\n', 0, 'utf-8');
    }
}


function constructAgent(agentConfig: AgentConfig): AIBase {
    const ctor = ais[agentConfig.className];
    return new ctor(agentConfig.options);
}

async function main() {
    const argv = await yargs(hideBin(process.argv))
        .demandCommand(4)
        .count("verbose")
        .argv;
    const [partyFile, agentFile, player1, player2] = argv._ as string[];
    const logFilePath = argv.log as string | undefined;
    const logLevel = logFilePath ? argv.verbose + 1 : 0;

    const parties: { _id: string, party: any }[] = loadJSON(partyFile);
    const agentConfigs: AgentConfig[] = loadJSON(agentFile);
    const players: Player[] = [null!, null!];
    for (const agentConfig of agentConfigs) {
        const agent = constructAgent(agentConfig);
        for (const party of parties) {
            const playerId = `${agentConfig.id}+${party._id}`;
            const player = { id: `${agentConfig.id}+${party._id}`, agent, party: party.party };
            if (playerId === player1) {
                players[0] = player;
            }
            if (playerId === player2) {
                players[1] = player;
            }
        }
    }
    const logFile = logFilePath ? fs.openSync(logFilePath, 'a') : undefined;

    oneBattle(players, logFile, logLevel);
}

main();
