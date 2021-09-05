// MCTSベース
// MCTSコアの実装は
// 「囲碁ディープラーニングプログラミング」 Max Pumperla, Kevin Ferguson 著、山岡忠夫訳を参考

const sim = require('../../Pokemon-Showdown/.sim-dist');

const PRNG = sim.PRNG;
import { AIBase, enumChoices, SearchLogEmitter, SearchLogLevel } from "./aiBase";
import { AIRandom2 } from "./aiRandom2";
import { playout } from "./playout";
import { invSideID, SideID, Sim } from "./sim";
import { assertNonNull } from "./util";

type MoveOrNull = string | null;

class MCTSNode {
    winCounts: {[sideid in SideID]: number};
    numRollouts: number;
    children: Map<MoveOrNull, MCTSNode>;
    unvisitedMoves: MoveOrNull[];
    isTerminal: boolean;
    winnerIfTerminal?: SideID;
    constructor(public prng: any, public gameState: Sim, public sideid: SideID, public opponentMove?: string | null) {
        this.winCounts = {'p1': 0, 'p2': 0};
        this.numRollouts = 0;
        this.children = new Map();
        const isTerminal = this.gameState.getEnded();
        this.isTerminal = isTerminal;
        if (isTerminal) {
            this.winnerIfTerminal = this.gameState.getWinner();
            if (this.winnerIfTerminal === undefined) {
                throw new Error('Cannot get winner on game end');
            }
            this.unvisitedMoves = [];
        } else {
            this.winnerIfTerminal = undefined;
            const choices = enumChoices(gameState.getRequest(sideid));
            if (choices.length > 0) {
                this.unvisitedMoves = choices.map((c) => c.key);
            } else {
                this.unvisitedMoves = [null]; // パスの1手だけを選択肢とみなす
            }
        }
        
    }

    popRandomUnvisitedMove(): MoveOrNull {
        const unvisitedLength = this.unvisitedMoves.length;
        if (unvisitedLength === 0) {
            throw new Error('No unvisited moves');
        }
        const index = unvisitedLength === 1 ? 0 : this.prng.next(unvisitedLength);
        const move = this.unvisitedMoves[index];
        this.unvisitedMoves.splice(index, 1);
        return move;
    }

    addChild(move: MoveOrNull): MCTSNode {
        // moveを適用した後の状態を生成
        // シミュレータは決定論的に動作するという仮定
        let newNode: MCTSNode;
        const opponentSideId = invSideID(this.sideid);
        if (this.opponentMove !== undefined) {
            // 自分と相手の行動が揃ったので1ターン進める
            const copySim = this.gameState.clone();
            const bothChoice = this.sideid === 'p1' ? [move, this.opponentMove] : [this.opponentMove, move];
            copySim.choose(bothChoice);
            newNode = new MCTSNode(this.prng, copySim, opponentSideId, undefined);
        } else {
            // シミュレータはまだ動かせない。相手の行動を決めるフェーズに進む
            newNode = new MCTSNode(this.prng, this.gameState, opponentSideId, move);
        }
        this.children.set(move, newNode);
        return newNode;
    }

    addRandomChild(): [MoveOrNull, MCTSNode] {
        const move = this.popRandomUnvisitedMove();
        const newNode = this.addChild(move);
        return [move, newNode];
    }

    canAddChild(): boolean {
        return this.unvisitedMoves.length > 0;
    }

    recordWin(winner: SideID): void {
        this.winCounts[winner]++;
        this.numRollouts++;
    }

    winningPct(sideid: SideID): number {
        return this.winCounts[sideid] / this.numRollouts;
    }
}

function uctScore(parentRollouts: number, childRollouts: number, winPct: number, temperature: number): number {
    const exploration = Math.sqrt(Math.log(parentRollouts) / childRollouts);
    return winPct + temperature * exploration;
}

const compressionWinnerTable = {
    p1: '1',
    p2: '2',
};

const compressionMoveTable: {[index: string]: string} = {
    'move 1': 'A',
    'move 2': 'B',
    'move 3': 'C',
    'move 4': 'D',
    'switch 1': 'a',
    'switch 2': 'b',
    'switch 3': 'c',
    'switch 4': 'd',
    'switch 5': 'e',
    'switch 6': 'f',
    null: '-',
};

function compressHistoryEntry(selectionPath: MoveOrNull[], winner: SideID): string {
    let s = compressionWinnerTable[winner];
    for (const m of selectionPath) {
        s += compressionMoveTable[m as string]; // nullを与えた場合"null"というキーとみなされる
    }
    return s;
}

export class AIMCTS extends AIBase {
    playoutSwitchRatio: number;
    playoutCount: number;
    temperature: number;
    constructor(options: { playoutSwitchRatio: number; playoutCount: number, temperature: number }) {
        super(options);
        this.playoutSwitchRatio = assertNonNull(options.playoutSwitchRatio);
        this.playoutCount = assertNonNull(options.playoutCount);
        this.temperature = assertNonNull(options.temperature);
    }

    private selectChild(node: MCTSNode): [MoveOrNull, MCTSNode] {
        let totalRollouts = 0;
        for (const child of node.children.values()) {
            totalRollouts += child.numRollouts;
        }
        let bestScore = -1;
        let bestNode: MCTSNode | undefined;
        let bestMove: MoveOrNull;
        for (const [move, child] of node.children.entries()) {
            // (childではなく)nodeからみた勝率が高いものを選ぶ
            const score = uctScore(totalRollouts, child.numRollouts, child.winningPct(node.sideid), this.temperature);
            if (score > bestScore) {
                bestScore = score;
                bestNode = child;
                bestMove = move;
            }
        }
        if (!bestNode) {
            throw new Error('selectChild for node without children');
        }
        return [bestMove!, bestNode];
    }

    go(sim: Sim, sideid: SideID, searchLogEmitter: SearchLogEmitter): string | null {
        const root = new MCTSNode(new PRNG(), sim, sideid, undefined);
        const playoutPolicy = new AIRandom2({ switchRatio: this.playoutSwitchRatio });
        const searchHistory: any = {};
        const saveHistory = searchLogEmitter.logLevel >= SearchLogLevel.VERBOSE;
        if (saveHistory) {
            searchHistory.sim = sim.serialize();
            searchHistory.playouts = [];
        }

        if (root.unvisitedMoves.length <= 1) {
            // 選択肢がない場合は探索しない
            return root.unvisitedMoves[0] || null;
        }

        for (let i = 0; i < this.playoutCount; i++) {
            let backupNodes: MCTSNode[] = [];
            let node = root;
            const selectionPath: MoveOrNull[] = [];
            backupNodes.push(node);
            while ((!node.canAddChild()) && (!node.isTerminal)) {
                let selectedMove: MoveOrNull;
                [selectedMove, node] = this.selectChild(node);
                backupNodes.push(node);
                selectionPath.push(selectedMove);
            }

            if (node.canAddChild()) {
                let randomMove: MoveOrNull;
                [randomMove, node] = node.addRandomChild();
                backupNodes.push(node);
                selectionPath.push(randomMove);
            }

            let winner: SideID;
            if (node.isTerminal) {
                winner = node.winnerIfTerminal!;
            } else {
                // プレイアウトする
                const copySim = node.gameState.clone();
                if (node.opponentMove !== undefined) {
                    // 片側の行動だけ決まっている状態なので、もう片方を埋めて1ターン進める
                    const leafChoice = playoutPolicy.go(copySim, node.sideid);
                    const bothChoice = node.sideid === 'p1' ? [leafChoice, node.opponentMove] : [node.opponentMove, leafChoice];
                    copySim.choose(bothChoice);
                }
                let { winner: playoutWinner } = playout(copySim, [playoutPolicy, playoutPolicy]);
                winner = playoutWinner || sideid;// 引き分けは珍しいので、とりあえずsideid側の勝ち扱い
            }

            for(let i = backupNodes.length-1; i >= 0; i--) {
                backupNodes[i].recordWin(winner);
            }

            if (saveHistory) {
                searchHistory.playouts.push(compressHistoryEntry(selectionPath, winner));
            }
        }

        let bestMove: string | null = null;
        let bestPct: number = -1.0;
        for (const [move, node] of root.children.entries()) {
            const pct = node.winningPct(sideid);
            if (pct > bestPct) {
                bestPct = pct;
                bestMove = move;
            }
        }
        if (searchLogEmitter.enabled) {
            const choices = enumChoices(sim.getRequest(sideid));
            if (saveHistory) {
                searchLogEmitter.emit({
                    type: 'MCTSSearchHistory',
                    payload: { searchHistory },
                });
            }
            searchLogEmitter.emit({
                type: 'MC',
                payload: {
                    winrates: choices.map((c, i) => ({ choice: c, winrate: root.children.get(c.key)?.winningPct(sideid) }))
                }
            });
        }

        return bestMove;
    }
}
