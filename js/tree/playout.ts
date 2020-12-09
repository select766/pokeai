import { AIBase } from "./aibase";
import { nPlayers, SideID, sideIDs, Sim } from "./sim";

interface PlayoutResult {
    winner: SideID | null;
    turns: number;
    totalChoices: [number, number];
}

const maxTurns = 100;

export function playout(sim: Sim, agents: AIBase[]): PlayoutResult {
    let totalChoices: [number, number] = [0, 0];
    while (!sim.getEnded()) {
        if (sim.getTurn() >= maxTurns) {
            return { winner: null, turns: sim.getTurn(), totalChoices };
        }
        const choices: (string | null)[] = [];
        for (let i = 0; i < nPlayers; i++) {
            const choice = agents[i].go(sim, sideIDs[i]);
            if (choice) {
                totalChoices[i]++;
            }
            choices.push(choice);
        }
        sim.choose(choices);
    }
    return { winner: sim.getWinner(), turns: sim.getTurn(), totalChoices };
}
