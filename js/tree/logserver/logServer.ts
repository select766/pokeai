import * as express from "express";
import * as cors from "cors";
const port = 3001;
const app = express();
app.use(cors());
app.use(express.json());

// curl http://localhost:3001 -X POST -H "Content-Type: application/json" -d '{"a":3,"b":4}'
app.post("/", function (req: express.Request, res: express.Response) {
  console.log(req.body);
  res.json({ sum: req.body.a + req.body.b });
});

app.listen(port, () => console.log(`API server running on port ${port}`));
