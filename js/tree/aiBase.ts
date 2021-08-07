import { BattleSearchLogEntry } from "./battleLogModel";
import { SideID, Sim } from "./sim";

export type ChoiceInfo = {
    key: string; // "move 1"
    type: 'move';
    moveInfo: {
        move: string; // "Dynamic Punch"
        id: string; // "dynamicpunch"
        pp: number;
        maxpp: number;
        target: string;
        disabled: boolean;
    }
} | {
    key: string; // "switch 3"
    type: 'switch';
    pokeInfo: {
        ident: string; // "p1: Octillery"
        details: string; // "Octillery, L55, M"
        conditions: string; // "146/198"
        active: boolean; // 場に出ているかどうか
        moves: string[]; // ["toxic","bubblebeam","flamethrower","mudslap"]
        item: string; // アイテムなしは""
    }
}

export function choiceToString(choiceInfo: ChoiceInfo): string {
    if (choiceInfo.type === 'move') {
        return choiceInfo.moveInfo.move;
    } else {
        return choiceInfo.pokeInfo.details.split(',')[0];
    }
}

export const SearchLogLevel = {
    DISABLED: 0,
    INFO: 1,
    VERBOSE: 2,
};

export interface SearchLogEmitter {
    enabled: boolean;
    /**
     * 0: disabled
     * 1: info
     * 2: verbose
     */
    logLevel: number;
    emit: (obj: BattleSearchLogEntry) => void;
}

export const SearchLogEmitterVoid: SearchLogEmitter = {
    enabled: false,
    logLevel: 0,
    emit: () => {},
};

export function enumChoices(request: any): ChoiceInfo[] {
    // 合法手列挙
    // シミュレータに送るコマンドと、目視確認用の説明（交代先ポケモン名か技名）
    // sim\tools\random-player-ai.ts を参考に、ダブルバトル・Z技などを除去
    const choices: ChoiceInfo[] = [];
    if (request.wait) {
    } else if (request.forceSwitch) {
        // シングルバトルではrequest.forceSwitch === [true]
        // request.side.pokemon[0] は今出ている（ちょうど瀕死になった）ポケモン
        for (let i = 1; i < request.side.pokemon.length; i++) {
            const pokemon = request.side.pokemon[i];
            if (!pokemon.condition.endsWith(' fnt')) {
                choices.push({ key: `switch ${i + 1}`, type: 'switch', pokeInfo: pokemon });
            }
        }
    } else if (request.active) {
        const moves = request.active[0].moves;
        for (let i = 0; i < moves.length; i++) {
            if (!moves[i].disabled) {
                choices.push({ key: `move ${i + 1}`, type: 'move', moveInfo: moves[i] });
            }
        }
        if (!request.active[0].trapped) {
            for (let i = 0; i < request.side.pokemon.length; i++) {
                const pokemon = request.side.pokemon[i];
                if (!pokemon.active && !pokemon.condition.endsWith(' fnt')) {
                    choices.push({ key: `switch ${i + 1}`, type: 'switch', pokeInfo: pokemon });
                }
            }
        }
    } else {
        // team preview?
        throw new Error('Unknown input for enumChoices');
    }

    return choices;
}

export class AIBase {
    constructor(options: {}) {
    }

    /**
     * 現局面に対する最善の行動を思考する
     * @param sim 現局面
     * @param sideid 自分のプレイヤー
     * @param searchLogEmitter 検索ログ出力先
     * @returns 最善の行動。"move 1", "move 2", ..., "switch 2", ...選択可能な行動がない状態ではnull。
     */
    go(sim: Sim, sideid: SideID, searchLogEmitter: SearchLogEmitter): string | null {
        const choices = enumChoices(sim.getRequest(sideid));
        if (choices.length > 0) {
            return choices[0].key;
        } else {
            return null;
        }
    }
}
