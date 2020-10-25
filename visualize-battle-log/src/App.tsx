import React, { useCallback, useRef, useState } from 'react';
import './App.scss';
import { BattleView } from './BattleView';
import { Battle, loadLog } from './model';

function App() {
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
      <form onSubmit={onFileSubmit}>
        JSON log: <input type="file" ref={fileRef} /><input type="submit" value="Submit" />
      </form>
      {battles.slice(0, 1).map((battle, i) => <BattleView key={i} battle={battle} />)}
    </div>
  );
}

export default App;
