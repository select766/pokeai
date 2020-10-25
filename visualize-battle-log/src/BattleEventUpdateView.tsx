import React, { useMemo } from 'react';
import { BattleEventUpdate } from "./model";
import { name2jp } from './name2jp';

export interface BattleEventUpdateViewProps {
  event: BattleEventUpdate;
}

export function BattleEventUpdateView({ event }: BattleEventUpdateViewProps): React.ReactElement {
  const eventItems = useMemo(() => {
    const updates = [...event.update];
    const result = [];
    while (updates.length > 0) {
      const update = updates.shift()!;// |move|p1a: Corsola|Earthquake|p2a: Azumarill
      const elems = update.split('|').slice(1); // ['move', 'p1a: Corsola', 'Earthquake', 'p2a: Azumarill'
      switch (elems[0]) {
        case 'move':
          result.push(`技 ${name2jp(elems[1].split(' ')[0])}${name2jp(elems[1].split(' ')[1])}の${name2jp(elems[2])}→${name2jp(elems[3].split(' ')[1])}`);
          break;
        case 'switch':
          // |switch|p2a: Azumarill|Azumarill, L50, M|206/206
          result.push(`交代 ${name2jp(elems[1].split(' ')[0])}${name2jp(elems[1].split(' ')[1])}`);
          break;
        case 'split':
          // 次の行は片方のプレイヤーにだけ見えるもので、現状不要
          updates.shift();
          break;
        case '-damage':
          // |-damage|p2a: Azumarill|169/206
          result.push(`ダメージ ${name2jp(elems[1].split(' ')[1])} ${elems[2]}`);
          break;
        case 'faint':
          // |faint|p1a: Beedrill
          result.push(`${name2jp(elems[1].split(' ')[1])}は倒れた`);
          break;
        case 'start':
          // |start
          result.push(`バトル開始`);
          break;
        case 'turn':
          // |turn|17
          result.push(`ターン${elems[1]}`);
          break;
        case '-crit':
          // |-crit|p2a: Azumarill
          result.push(`きゅうしょにあたった`)
          break;
        case '-supereffective':
          // |-supereffective|p2a: Typhlosion
          result.push(`効果は抜群だ`)
          break;
        case '-resisted':
          // |-resisted|p1a: Corsola
          result.push(`効果はいまひとつのようだ`);
          break;
        case '-immune':
          // |-immune|p2a: Crobat
          result.push(`効果はないようだ`);
          break;
        case 'win':
          // |win|p2
          result.push(`${elems[1]}の勝ち`);
          break;
        case '':
        case 'player':
        case 'teamsize':
        case 'gametype':
        case 'gen':
        case 'tier':
        case 'rule':
        case 'upkeep':
        case 'debug':
          break;
        default:
          console.warn(`Unhandled update '${update}'`);
          break;
      }
    }
    return result;
  }, [event.update]);
  return <div className="battleEventUpdateView">
    <table>
      <tbody>
        {eventItems.map((update, i) => <tr key={i}><td>{update}</td></tr>)}
      </tbody>
    </table>
  </div>
}
