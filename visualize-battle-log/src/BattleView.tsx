import React from 'react';
import { BattleEventChoiceView } from './BattleEventChoiceView';
import { BattleEventUpdateView } from './BattleEventUpdateView';
import { Battle } from "./model";
import { PlayerView } from './PlayerView';

export interface BattleProps {
  battle: Battle;
}

export function BattleView({ battle }: BattleProps): React.ReactElement {
  return <div>
    {`${battle.agents.p1.player_id} vs ${battle.agents.p2.player_id}`}
    <div>
      {[battle.agents.p1, battle.agents.p2].map((player, i) => <PlayerView key={i} player={player} />)}
    </div>
    <div>
      {battle.events.map((ev, i) => <div key={i}>{ev.type === 'update' ? <BattleEventUpdateView event={ev}/> : <BattleEventChoiceView event={ev}/>}</div>)}
    </div>
    <div>
      winner: {battle.end.winner}
    </div>
  </div>
}
