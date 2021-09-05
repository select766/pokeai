import React from "react";
import { BrowserRouter, Route } from "react-router-dom";
import "./App.scss";
import { MCTSLogPage } from "./MCTSLogPage";
import { PageList } from "./PageList";
import { RLLogPage } from "./RLLogPage";

function App() {
  return (
    <BrowserRouter>
      <Route path="/mcts" component={MCTSLogPage} />
      <Route path="/rl" component={RLLogPage} />
      <Route path="/" exact component={PageList} />
    </BrowserRouter>
  );
}

export default App;
