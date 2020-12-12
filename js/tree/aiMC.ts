// 原始モンテカルロ法ベース

const sim = require('../../Pokemon-Showdown/.sim-dist');

const PRNG = sim.PRNG;
import { AIBase, choiceToString, SearchLogEmitter } from "./aibase";
import { AIRandom2 } from "./aiRandom2";
import { argsort } from "./mathUtil";
import { playout } from "./playout";
import { invSideID, SideID, Sim } from "./sim";


export class AIMC extends AIBase {
    playoutSwitchRatio: number;
    playoutCount: number;
    constructor(options: { playoutSwitchRatio: number; playoutCount: number }) {
        super(options);
        this.playoutSwitchRatio = options.playoutSwitchRatio;
        this.playoutCount = options.playoutCount;
    }

    go(sim: Sim, sideid: SideID, searchLogEmitter: SearchLogEmitter): string | null {
        const choices = this.enumChoices(sim.getRequest(sideid));
        const playoutPolicy = new AIRandom2({ switchRatio: this.playoutSwitchRatio });
        if (choices.length > 0) {
            const playoutPerAction = Math.floor(this.playoutCount / choices.length);
            const winCounts = (new Array(choices.length)).fill(0);
            for (let c = 0; c < choices.length; c++) {
                for (let i = 0; i < playoutPerAction; i++) {
                    const copySim = sim.clone();
                    const opponentChoice = playoutPolicy.go(copySim, invSideID(sideid));
                    const bothChoice = sideid === 'p1' ? [choices[c].key, opponentChoice] : [opponentChoice, choices[c].key];
                    copySim.choose(bothChoice);
                    const { winner } = playout(copySim, [playoutPolicy, playoutPolicy]);
                    if (winner === sideid) {
                        winCounts[c]++;
                    }
                }
            }
            if (searchLogEmitter.enabled) {
                searchLogEmitter.emit({
                    type: 'MC',
                    payload: {
                        winrates: choices.map((c, i) => ({ choice: c, winrate: (winCounts[i] / playoutPerAction) }))
                    }
                });
            }
            const bestIdx = argsort(winCounts)[winCounts.length - 1];
            return choices[bestIdx].key;
        } else {
            return null;
        }
    }
}
