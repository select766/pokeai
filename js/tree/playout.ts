import { AIBase } from "./aibase";
import { nPlayers, SideID, sideIDs, Sim } from "./sim";

const maxTurns = 100;

export function playout(sim: Sim, agents: AIBase[]): SideID | null {
    while (!sim.getEnded()) {
        if (sim.getTurn() >= maxTurns) {
            return null;
        }
        const choices: (string|null)[] = [];
        for (let i = 0; i < nPlayers; i++) {
            choices.push(agents[i].go(sim, sideIDs[i]));
        }
        sim.choose(choices);
    }
    return sim.getWinner();
}
