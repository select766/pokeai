// MCTSベース
// MCTSコアの実装は
// 「囲碁ディープラーニングプログラミング」 Max Pumperla, Kevin Ferguson 著、山岡忠夫訳を参考

const sim = require('../../Pokemon-Showdown/.sim-dist');

const PRNG = sim.PRNG;
import { AIBase, choiceToString, enumChoices, SearchLogEmitter } from "./aiBase";
import { AIRandom2 } from "./aiRandom2";
import { argsort } from "./mathUtil";
import { playout } from "./playout";
import { invSideID, SideID, Sim } from "./sim";
import { assertNonNull } from "./util";

class MCTSNode {
    winCounts: {[sideid in SideID]: number};
    numRollouts: number;
    children: Map<string|null, MCTSNode>;
    unvisitedMoves: (string|null)[];
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

    addRandomChild(): MCTSNode {
        const unvisitedLength = this.unvisitedMoves.length;
        if (unvisitedLength === 0) {
            throw new Error('No unvisited moves');
        }
        const index = unvisitedLength === 1 ? 0 : this.prng.next(unvisitedLength);
        const move = this.unvisitedMoves[index];
        this.unvisitedMoves.splice(index, 1);
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

    private selectChild(node: MCTSNode): MCTSNode {
        let totalRollouts = 0;
        for (const child of node.children.values()) {
            totalRollouts += child.numRollouts;
        }
        let bestScore = -1;
        let bestNode: MCTSNode | undefined;
        for (const child of node.children.values()) {
            // (childではなく)nodeからみた勝率が高いものを選ぶ
            const score = uctScore(totalRollouts, child.numRollouts, child.winningPct(node.sideid), this.temperature);
            if (score > bestScore) {
                bestScore = score;
                bestNode = child;
            }
        }
        if (!bestNode) {
            throw new Error('selectChild for node without children');
        }
        return bestNode;
    }

    go(sim: Sim, sideid: SideID, searchLogEmitter: SearchLogEmitter): string | null {
        const root = new MCTSNode(new PRNG(), sim, sideid, undefined);
        const playoutPolicy = new AIRandom2({ switchRatio: this.playoutSwitchRatio });

        if (root.unvisitedMoves.length <= 1) {
            // 選択肢がない場合は探索しない
            return root.unvisitedMoves[0] || null;
        }

        for (let i = 0; i < this.playoutCount; i++) {
            let backupNodes: MCTSNode[] = [];
            let node = root;
            backupNodes.push(node);
            while ((!node.canAddChild()) && (!node.isTerminal)) {
                node = this.selectChild(node);
                backupNodes.push(node);
            }

            if (node.canAddChild()) {
                node = node.addRandomChild();
                backupNodes.push(node);
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
