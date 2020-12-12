import { performance } from 'perf_hooks';
import { AIBase, SearchLogEmitter, SearchLogEmitterVoid } from "./aibase";
import { BattleEvent } from "./battleLogModel";
import { nPlayers, SideID, sideIDs, Sim } from "./sim";

interface PlayoutResult {
    winner: SideID | null;
    turns: number;
    totalChoices: [number, number];
    log?: BattleEvent[];
}

const maxTurns = 100;

class SearchLogEmitterImpl implements SearchLogEmitter {
    enabled: boolean;
    entries: any[];

    constructor() {
        this.enabled = true;
        this.entries = [];
    }

    emit(obj: any):void{
        this.entries.push(obj);
    }
}

export function playout(sim: Sim, agents: AIBase[], getLog: boolean = false): PlayoutResult {
    let totalChoices: [number, number] = [0, 0];
    let battleEvents: BattleEvent[] = [];
    let battleLogPos = 0;
    const pushUpdate = getLog ? () => {
        const l = sim.getLog();
        battleEvents.push({
            type: 'update',
            update: l.slice(battleLogPos)
        });
        battleLogPos = l.length;
    } : () => {};

    pushUpdate();
    while (!sim.getEnded()) {
        if (sim.getTurn() >= maxTurns) {
            break;
        }
        const choices: (string | null)[] = [];
        for (let i = 0; i < nPlayers; i++) {
            const emitter = getLog ? new SearchLogEmitterImpl() : SearchLogEmitterVoid;
            const timeStart = performance.now();
            const choice = agents[i].go(sim, sideIDs[i], emitter);
            const searchTime = performance.now() - timeStart;
            if (choice) {
                totalChoices[i]++;
                if (getLog) {
                    battleEvents.push({
                        type: 'choice',
                        choice: {
                            player: sideIDs[i],
                            request: sim.getRequest(sideIDs[i]),
                            choice,
                            searchLog: (emitter as SearchLogEmitterImpl).entries,
                            searchTime,
                        }
                    });
                }
            }
            choices.push(choice);
        }
        sim.choose(choices);
        pushUpdate();
    }

    return { winner: sim.getWinner() || null, turns: sim.getTurn(), totalChoices, log: battleEvents };
}
