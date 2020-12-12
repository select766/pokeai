const sim = require('../../Pokemon-Showdown/.sim-dist');

const PRNG = sim.PRNG;
import { AIBase } from "./aiBase";
import { SideID, Sim } from "./sim";


export class AIRandom2 extends AIBase {
    switchRatio: number;
    constructor(options: { switchRatio: number }) {
        super(options);
        this.switchRatio = options.switchRatio;
    }

    go(sim: Sim, sideid: SideID): string | null {
        const choices = this.enumChoices(sim.getRequest(sideid));
        if (choices.length > 0) {
            const prng = new PRNG();
            const choicesMove = choices.filter((v) => v.type === 'move');
            const choicesSwitch = choices.filter((v) => v.type === 'switch');
            let candChoices: typeof choices;
            if (choicesSwitch.length) {
                if (choicesMove.length) {
                    if (prng.next() < this.switchRatio) {
                        candChoices = choicesSwitch;
                    } else {
                        candChoices = choicesMove;
                    }
                } else {
                    candChoices = choicesSwitch;
                }
            } else {
                candChoices = choicesMove;
            }
            const idx = prng.next(candChoices.length);
            return candChoices[idx].key;
        } else {
            return null;
        }
    }
}
