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
      const updateType = elems[0];
      switch (updateType) {
        case 'move':
          // "p2a: Mr. Mime"があるのでsplit(" ")は使わない
          result.push(<li key={result.length} className={updateType}>{`技 ${name2jp(elems[1].substring(0, 4))}${name2jp(elems[1].substring(5))}の${name2jp(elems[2])}→${name2jp(elems[3].substring(5))}`}</li>);
          break;
        case 'switch':
          // |switch|p2a: Azumarill|Azumarill, L50, M|206/206
          result.push(<li key={result.length} className={updateType}>{`交代 ${name2jp(elems[1].substring(0, 4))}${name2jp(elems[1].substring(5))}`}</li>);
          break;
        case 'split':
          // 次の行は片方のプレイヤーにだけ見えるもので、現状不要
          updates.shift();
          break;
        case '-damage':
          // |-damage|p2a: Azumarill|169/206
          result.push(<li key={result.length} className={updateType}>{`ダメージ ${name2jp(elems[1].substring(5))} ${elems[2]}`}</li>);
          break;
        case 'faint':
          // |faint|p1a: Beedrill
          result.push(<li key={result.length} className={updateType}>{`${name2jp(elems[1].substring(5))}は倒れた`}</li>);
          break;
        case 'start':
          // |start
          result.push(<li key={result.length} className={updateType}>{`バトル開始`}</li>);
          break;
        case 'turn':
          // |turn|17
          result.push(<li key={result.length} className={updateType}>{`ターン${elems[1]}`}</li>);
          break;
        case '-crit':
          // |-crit|p2a: Azumarill
          result.push(<li key={result.length} className={updateType}>{`きゅうしょにあたった`}</li>)
          break;
        case '-supereffective':
          // |-supereffective|p2a: Typhlosion
          result.push(<li key={result.length} className={updateType}>{`効果は抜群だ`}</li>)
          break;
        case '-resisted':
          // |-resisted|p1a: Corsola
          result.push(<li key={result.length} className={updateType}>{`効果はいまひとつのようだ`}</li>);
          break;
        case '-immune':
          // |-immune|p2a: Crobat
          result.push(<li key={result.length} className={updateType}>{`効果はないようだ`}</li>);
          break;
        case '-status':
          // |-status|p1a: Gengar|frz
          result.push(<li key={result.length} className={updateType}>{`状態異常 ${name2jp(elems[1].substring(5))} ${elems[2]}`}</li>);
          break;
        case '-curestatus':
          // |-curestatus|p1a: Stantler|frz|[msg]
          result.push(<li key={result.length} className={updateType}>{`状態異常回復 ${name2jp(elems[1].substring(5))} ${elems[2]}`}</li>);
          break;
        case '-boost':
          // |-boost|p1a: Umbreon|evasion|1
          result.push(<li key={result.length} className={updateType}>{`ランク上昇 ${name2jp(elems[1].substring(5))} ${elems[2]}${elems[3]}`}</li>);
          break;
        case '-unboost':
          // |-unboost|p2a: Lapras|accuracy|1
          result.push(<li key={result.length} className={updateType}>{`ランク下降 ${name2jp(elems[1].substring(5))} ${elems[2]}${elems[3]}`}</li>);
          break;
        case '-heal':
          // |-heal|p1a: Gengar|124/166|[from] drain|[of] p2a: Lapras
          result.push(<li key={result.length} className={updateType}>{`回復 ${name2jp(elems[1].substring(5))} ${elems[2]}${elems[3]}${elems[4]}`}</li>);
          break;
        case '-miss':
          // |-miss|p1a: Electabuzz
          result.push(<li key={result.length} className={updateType}>{`外れた ${name2jp(elems[1].substring(5))}`}</li>);
          break;
        case '-fail':
          // |-fail|p1a: Electabuzz|tox
          result.push(<li key={result.length} className={updateType}>{`失敗 ${name2jp(elems[1].substring(5))} ${elems[2]}`}</li>);
          break;
        case '-mustrecharge':
          // |-mustrecharge|p1a: Butterfree
          result.push(<li key={result.length} className={updateType}>{`反動発生 ${name2jp(elems[1].substring(5))}`}</li>);
          break;
        case '-start':
          // |-start|p2a: Raichu|confusion|[silent]
          result.push(<li key={result.length} className={updateType}>{`状態変化 ${name2jp(elems[1].substring(5))} ${elems[2]}${elems[3]}`}</li>);
          break;
        case '-prepare':
          // |-prepare|p2a: Togetic|Solar Beam|p1a: Lapras
          result.push(<li key={result.length} className={updateType}>{`溜め ${name2jp(elems[1].substring(5))}の${name2jp(elems[2])}→${name2jp(elems[3].substring(5))}`}</li>);
          break;

        case 'cant':
          // |cant|p2a: Golduck|frz
          result.push(<li key={result.length} className={updateType}>{`行動不能 ${name2jp(elems[1].substring(5))} ${elems[2]}`}</li>);
          break;
        case 'win':
          // |win|p2
          result.push(<li key={result.length} className={updateType}>{`${elems[1]}の勝ち`}</li>);
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
    <ul>
      {eventItems}
    </ul>
  </div>
}
