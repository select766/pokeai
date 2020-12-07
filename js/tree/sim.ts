const sim = require('../../Pokemon-Showdown/.sim-dist');

const Dex = sim.Dex;
const Battle = sim.Battle;

export type Side = 0 | 1;
export type SideID = 'p1' | 'p2';
export const sideIDs = ['p1', 'p2'] as SideID[];
export const nPlayers = 2;
export const sideidToSide = { p1: 0, p2: 1 };
export function invSideID(sideid: SideID): SideID {
    return {p1: 'p2', p2: 'p1'}[sideid] as SideID;
}
export function invSide(side: Side): Side {
    return (1 - side) as Side;
}

export class Sim {
    constructor(private battle: any) {
    }

    static fromParty(parties: any[], seed?: any): Sim {
        const battle = new Battle({ formatid: "gen2customgame", seed });

        const party1spec = { 'name': 'p1', 'team': Dex.packTeam(parties[0]) };
        const party2spec = { 'name': 'p2', 'team': Dex.packTeam(parties[1]) };

        battle.setPlayer('p1', party1spec);
        battle.setPlayer('p2', party2spec);

        return new Sim(battle);
    }

    clone(): Sim {
        const battle = Battle.fromJSON(this.battle.toJSON());
        return new Sim(battle);
    }

    choose(choices: (string | null)[]): void {
        for (let i = 0; i < nPlayers; i++) {
            const choice = choices[i];
            if (choice) {
                if (!this.battle.choose(sideIDs[i], choice)) {
                    throw new Error('Battle.choose error');
                }
            }
        }
    }

    getEnded(): boolean {
        return this.battle.ended;
    }

    getWinner(): SideID | undefined {
        return this.battle.winner;
    }

    getTurn(): number {
        return this.battle.turn;
    }

    /**
     * バトル開始からのログを取得する
     */
    getLog(): string[] {
        return this.battle.log;
    }

    getRequest(sideid: SideID): any {
        return this.battle.sides[sideidToSide[sideid]].activeRequest;
    }
}
