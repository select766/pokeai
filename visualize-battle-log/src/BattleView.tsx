import React, { useCallback, useState } from 'react';
import { BattleEventChoiceView } from './BattleEventChoiceView';
import { BattleEventUpdateView } from './BattleEventUpdateView';
import { Battle } from "./model";
import { PlayerView } from './PlayerView';

export interface BattleProps {
  battle: Battle;
}

export function BattleView({ battle }: BattleProps): React.ReactElement {
  const [opened, setOpened] = useState(false);
  const onOpenClick = useCallback(() => {
    setOpened(!opened);
  }, [opened]);

  return <div>
    <div>
      {[battle.agents.p1, battle.agents.p2].map((player, i) => <PlayerView key={i} player={player} />)}
    </div>
    <div>
      <button type="button" onClick={onOpenClick}>↓展開</button>
    </div>
    {opened &&
      <div>
        <div>
          {battle.events.map((ev, i) => <div key={i}>{ev.type === 'update' ? <BattleEventUpdateView event={ev} /> : <BattleEventChoiceView event={ev} />}</div>)}
        </div>
        <div>
          winner: {battle.end.winner}
        </div>
      </div>
    }
    <div>
      <button type="button" onClick={onOpenClick}>↑展開</button>
    </div>
    <hr />
  </div>
}
