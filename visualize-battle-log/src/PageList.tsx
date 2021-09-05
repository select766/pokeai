import { Link } from "react-router-dom";

export function PageList() {
  return (
    <div>
      <ul>
        <li>
          <Link to="/mcts">MCTS log visualizer</Link>
        </li>
        <li>
          <Link to="/rl">RL log visualizer</Link>
        </li>
      </ul>
    </div>
  );
}
