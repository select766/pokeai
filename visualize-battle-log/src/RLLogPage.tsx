import React, { useCallback, useRef, useState } from 'react';
import { BattleView } from './BattleView';
import { Battle, loadLog } from './model';

export function RLLogPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [battles, setBattles] = useState<Battle[]>([]);
  const onFileSubmit = useCallback(async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (file) {
      setBattles(await loadLog(file));
    }
  }, []);
  return (
    <div className="App">
      <form onSubmit={onFileSubmit} className="printNone">
        JSON log: <input type="file" ref={fileRef} /><input type="submit" value="Submit" />
      </form>
      {battles.slice(0, 100).map((battle, i) => <BattleView key={i} battle={battle} />)}
    </div>
  );
}
