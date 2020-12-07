// モンテカルロ法の実行結果表示

import { AIMC } from "./aiMC";
import { AIRandom2 } from "./aiRandom2";
import { playout } from "./playout";
import { Sim } from "./sim";

const party1 = [
    {
        "name": "octillery",
        "species": "octillery",
        "moves": [
            "toxic",
            "bubblebeam",
            "flamethrower",
            "mudslap"
        ],
        "ability": "No Ability",
        "evs": {
            "hp": 255,
            "atk": 255,
            "def": 255,
            "spa": 255,
            "spd": 255,
            "spe": 255
        },
        "ivs": {
            "hp": 30,
            "atk": 30,
            "def": 30,
            "spa": 30,
            "spd": 30,
            "spe": 30
        },
        "item": "",
        "level": 55,
        "shiny": false,
        "gender": "M",
        "nature": ""
    }
];
const party2 = [
    {
        "name": "granbull",
        "species": "granbull",
        "moves": [
            "dynamicpunch",
            "thunderpunch",
            "rocksmash",
            "thunderbolt"
        ],
        "ability": "No Ability",
        "evs": {
            "hp": 255,
            "atk": 255,
            "def": 255,
            "spa": 255,
            "spd": 255,
            "spe": 255
        },
        "ivs": {
            "hp": 30,
            "atk": 30,
            "def": 30,
            "spa": 30,
            "spd": 30,
            "spe": 30
        },
        "item": "",
        "level": 55,
        "shiny": false,
        "gender": "M",
        "nature": ""
    }
];


function main() {
    const sim = Sim.fromParty([party1, party2]);
    const agentMC = new AIMC({playoutCount: 100, playoutSwitchRatio: 0});
    const agentRandom = new AIRandom2({switchRatio:0});
    const result = playout(sim,[agentMC, agentRandom]);
    console.log('result', result);
}

main();
