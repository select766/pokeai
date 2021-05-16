import { AIBase } from "./aiBase";
import { AIMC } from "./aiMC";
import { AIMCTS } from "./aiMCTS";
import { AIRandom } from "./aiRandom";
import { AIRandom2 } from "./aiRandom2";

export const ais: { [key: string]: typeof AIBase } = {
  AIRandom: AIRandom,
  AIRandom2: AIRandom2,
  AIMC: AIMC,
  AIMCTS: AIMCTS,
};
