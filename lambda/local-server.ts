import http from "http";
import { handler } from "./index";

const port = process.env.PORT ? Number(process.env.PORT) : 8080;

const server = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/invoke") {
    try {
      let body = "";
      req.on("data", (chunk) => {
        body += chunk;
      });
      req.on("end", async () => {
        let event: any = {};
        try {
          event = body ? JSON.parse(body) : {};
        } catch (e) {}
        const result = await handler(event);
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(result));
      });
    } catch (err: any) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: err?.message || "Invocation error" }));
    }
  } else if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
  } else {
    res.writeHead(404);
    res.end();
  }
});

server.listen(port, () => {
  console.log(`Local Lambda emulation listening on :${port}`);
});
