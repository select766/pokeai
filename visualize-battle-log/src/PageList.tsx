import { Link } from "react-router-dom";

export function PageList() {
  return (
    <div>
      <ul>
        <li>
          <Link to="/rl">RL log visualizer</Link>
        </li>
      </ul>
    </div>
  );
}
