import React, { useEffect, useState } from "react";

export function MCTSLogPage() {
  const [response, setResponse] = useState<string>("Loading");
  useEffect(() => {
    (async () => {
      const f = await fetch("http://localhost:3001/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ a: 3, b: 4 }),
      });
      const res = await f.json();
      setResponse(res.sum.toString());
    })();
  }, []);
  return (
    <div className="App">
      MCTS Log Page TODO
      <p>3+4={response}</p>
    </div>
  );
}
