// レーティングバトル、マルチプロセス版
import * as fs from "fs";
import * as cluster from "cluster";
import * as os from "os";

import { AIBase } from "./aiBase";
import { ais } from "./ais";
import { BattleEvent, BattleLog } from "./battleLogModel";
import { argsort, rnorm } from "./mathUtil";
import { playout } from "./playout";
import { SideID, Sim } from "./sim";
import { loadJSON, saveJSON } from "./util";

interface Player {
  id: string;
  agentConfig: any;
  party: any;
}

interface AgentConfig {
  id: string;
  className: string;
  options: any;
}

interface JobRequest {
  leftPlayer: Player;
  rightPlayer: Player;
  left: number;
  right: number;
  getLog: boolean;
}

interface JobResponse {
  left: number;
  right: number;
  winner: SideID | null;
  log?: BattleEvent[];
}

/**
 * 指定した数のワーカを起動し、起動の完了を待つ。
 * @param {number} nWorkers
 * @returns
 */
function startWorkers(nWorkers: number): Promise<cluster.Worker[]> {
  return new Promise((resolve) => {
    const workers: cluster.Worker[] = [];
    for (let i = 0; i < nWorkers; i++) {
      const worker = cluster.fork();
      worker.on("online", () => {
        workers.push(worker);
        if (workers.length === nWorkers) {
          resolve(workers);
        }
      });
    }
  });
}

function runTasks(tasks: any[], workers: cluster.Worker[]): Promise<any[]> {
  const remainingTasks = tasks.slice();
  const nTasks = remainingTasks.length;

  return new Promise((resolve) => {
    const results: any[] = []; // 完了順のため、必要に応じソート
    cluster.on("message", (worker, message) => {
      results.push(message);
      if (remainingTasks.length > 0) {
        // ワーカに次のジョブを与える
        worker.send(remainingTasks.pop());
      }
      if (results.length === nTasks) {
        resolve(results);
      }
    });
    for (const worker of workers) {
      const taskData = remainingTasks.pop();
      if (taskData !== undefined) {
        worker.send(taskData);
      }
    }
  });
}

function jobFunction(data: JobRequest): JobResponse {
  const sim = Sim.fromParty([data.leftPlayer.party, data.rightPlayer.party]);
  const { winner, log } = playout(
    sim,
    [
      constructAgent(data.leftPlayer.agentConfig),
      constructAgent(data.rightPlayer.agentConfig),
    ],
    data.getLog
  );
  return { winner, log, left: data.left, right: data.right };
}

function worker() {
  process.on("message", (data: JobRequest) => {
    const result = jobFunction(data);
    process.send!(result);
  });
}

async function ratingBattle(
  workers: cluster.Worker[],
  players: Player[],
  matchCount: number,
  logFile?: number
): Promise<number[]> {
  const rates: number[] = new Array(players.length).fill(1500);

  for (let i = 0; i < matchCount; i++) {
    console.log(`${new Date()}:${i}/${matchCount}`);
    const ratesWithRandom = rates.map((r) => r + rnorm() * 200);
    const ranking = argsort(ratesWithRandom);
    const jobRequests: JobRequest[] = [];
    for (let j = 0; j < players.length; j += 2) {
      const left = ranking[j];
      const right = ranking[j + 1];
      jobRequests.push({
        leftPlayer: players[left],
        rightPlayer: players[right],
        left,
        right,
        getLog: !!logFile,
      });
    }
    const jobResponses: JobResponse[] = await runTasks(jobRequests, workers);
    for (const { winner, log, left, right } of jobResponses) {
      if (winner) {
        const left_winrate =
          1.0 / (1.0 + 10.0 ** ((rates[right] - rates[left]) / 400.0));
        let left_incr;
        if (winner === "p1") {
          left_incr = 32 * (1.0 - left_winrate);
        } else {
          left_incr = 32 * -left_winrate;
        }
        rates[left] += left_incr;
        rates[right] -= left_incr;
      }
      if (logFile && log) {
        const entry: BattleLog = {
          agents: {
            p1: { player_id: players[left].id, party: players[left].party },
            p2: { player_id: players[right].id, party: players[right].party },
          },
          events: log,
          end: { winner: winner || "" },
        };
        fs.writeSync(logFile, JSON.stringify(entry) + "\n", 0, "utf-8");
      }
    }
  }

  return rates;
}

function constructAgent(agentConfig: AgentConfig): AIBase {
  const ctor = ais[agentConfig.className];
  return new ctor(agentConfig.options);
}

async function main() {
  const [, , partyFile, agentFile, battleCountStr, resultFile, logFilePath] =
    process.argv;
  const parties: { _id: string; party: any }[] = loadJSON(partyFile);
  const agentConfigs: AgentConfig[] = loadJSON(agentFile);
  const players: Player[] = [];
  for (const agentConfig of agentConfigs) {
    for (const party of parties) {
      players.push({
        id: `${agentConfig.id}+${party._id}`,
        agentConfig,
        party: party.party,
      });
    }
  }
  const logFile = logFilePath ? fs.openSync(logFilePath, "a") : undefined;

  const workers = await startWorkers(os.cpus().length); // CPUコア数分並列起動

  console.time("all battles");
  const ratings = await ratingBattle(
    workers,
    players,
    Number(battleCountStr),
    logFile
  );
  console.timeEnd("all battles");
  const results: { id: string; rate: number }[] = [];
  for (let i = 0; i < players.length; i++) {
    results.push({ id: players[i].id, rate: ratings[i] });
  }
  if (logFile) {
    fs.closeSync(logFile);
  }
  saveJSON(resultFile, results);
  cluster.disconnect(); // ワーカを終了させる。これがないと、この関数を抜けてもプロセスが終了しない
}

if (cluster.isMaster) {
  main();
} else {
  worker();
}
