import React from 'react';
import { BattleEventChoice } from "./model";
import { name2jp } from './name2jp';

export interface BattleEventChoiceViewProps {
  event: BattleEventChoice;
}

export function BattleEventChoiceView({ event }: BattleEventChoiceViewProps): React.ReactElement {
  if (!event.choice.possible_actions) {
    return <div className="battleEventChoiceView">{event.choice.player}: 選択肢なし</div>
  }
  const line1 = [<td key="player">{event.choice.player}</td>];
  const line2 = [<td key="player"></td>];

  const sideActiveStatus = event.choice.battle_status.side_statuses[event.choice.battle_status.side_friend].active;
  let sidePokeStatus = `${sideActiveStatus.hp_current}/${sideActiveStatus.hp_max} ${sideActiveStatus.status} ${sideActiveStatus.volatile_statuses.join(' ')}`;
  for (const key of Object.keys(sideActiveStatus.ranks)) {
    const rank = sideActiveStatus.ranks[key as keyof typeof sideActiveStatus.ranks];
    if (rank !== 0) {
      sidePokeStatus += ` ${key}${rank > 0 ? '+' : ''}${rank}`;
    }
  }
  let firstMove = true;
  for (let i = 0; i < event.choice.possible_actions.length; i++) {
    const action = event.choice.possible_actions[i];
    const q_value = event.choice.q_func?.q_func[i]?.toFixed(2) || '';
    if (action.switch) {
      const movesJp = action.allMoves.map(name2jp);
      line1.push(<td key={action.simulator_key} className={action.simulator_key === event.choice.choice ? 'actualChoice' : ''}>{`${name2jp(action.poke)} ${q_value}`}</td>);
      line2.push(<td key={action.simulator_key}>{movesJp[0]},{movesJp[1]}<br />{movesJp[2]},{movesJp[3]}</td>);
    } else {
      if (firstMove) { // move 1がdisabledの可能性があるため、simulator_key==='move 1'は不適切
        const n_moves = event.choice.possible_actions.filter((v) => !v.switch).length;
        line1.push(<td key={action.simulator_key} colSpan={n_moves}>{`${name2jp(action.poke)} ${sidePokeStatus}`}</td>);
        firstMove = false;
      }
      line2.push(<td key={action.simulator_key} className={action.simulator_key === event.choice.choice ? 'actualChoice' : ''}>{`${name2jp(action.move)}`}<br />{q_value}</td>);
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
