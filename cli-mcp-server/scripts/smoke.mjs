import { spawn } from "node:child_process";
import { once } from "node:events";

const port = process.env.LARK_CLI_MCP_PORT ?? "3017";
const child = spawn(process.execPath, ["src/server.js"], {
  cwd: new URL("..", import.meta.url),
  env: { ...process.env, LARK_CLI_MCP_PORT: port },
  stdio: ["ignore", "pipe", "pipe"]
});

try {
  await waitForHealth(port);
  const response = await fetch(`http://127.0.0.1:${port}/health`);
  const json = await response.json();
  if (!json.ok) throw new Error(`health returned ${JSON.stringify(json)}`);
  console.log(`smoke ok: ${json.name} ${json.version}`);
} finally {
  child.kill("SIGTERM");
  await once(child, "close").catch(() => {});
}

async function waitForHealth(port) {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/health`);
      if (response.ok) return;
    } catch {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error("server did not become healthy");
}
