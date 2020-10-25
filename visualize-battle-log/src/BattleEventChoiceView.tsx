import React from 'react';
import { BattleEventChoice } from "./model";
import { name2jp } from './name2jp';

export interface BattleEventChoiceViewProps {
  event: BattleEventChoice;
}

export function BattleEventChoiceView({ event }: BattleEventChoiceViewProps): React.ReactElement {
  if (!event.choice.possible_actions) {
    return <div>{event.choice.player}: 選択肢なし</div>
  }
  const line1 = [<td key="player">{event.choice.player}</td>];
  const line2 = [<td key="player"></td>];
  for (const action of event.choice.possible_actions) {
    if (action.switch) {
      line1.push(<td key={action.simulator_key}>{`${name2jp(action.poke)}`}</td>);
      line2.push(<td key={action.simulator_key}></td>);
    } else {
      if (action.simulator_key === 'move 1') {
        // TODO: 技が4つでない場合
        line1.push(<td key={action.simulator_key} colSpan={4}>{`${name2jp(action.poke)}`}</td>);
      }
      line2.push(<td key={action.simulator_key}>{`${name2jp(action.move)}`}</td>);
    }
  }
  return <div className="battleEventChoiceView">
    <table>
      <tbody>
        <tr>{line1}
        </tr>
        <tr>
          {line2}
        </tr>
      </tbody>
    </table>
  </div>
}
