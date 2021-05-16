const sim = require('../../Pokemon-Showdown/.sim-dist');

const PRNG = sim.PRNG;
import { AIBase, enumChoices } from "./aiBase";
import { SideID, Sim } from "./sim";


export class AIRandom extends AIBase {
    constructor(options: {}) {
        super(options);
    }

    go(sim: Sim, sideid: SideID): string | null {
        const choices = enumChoices(sim.getRequest(sideid));
        if (choices.length > 0) {
            const prng = new PRNG();
            const idx = prng.next(choices.length);
            return choices[idx].key;
        } else {
            return null;
        }
    }
}
