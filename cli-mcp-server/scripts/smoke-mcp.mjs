import { spawn } from "node:child_process";
import { once } from "node:events";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const port = process.env.LARK_CLI_MCP_PORT ?? "3018";
const child = spawn(process.execPath, ["src/server.js"], {
  cwd: new URL("..", import.meta.url),
  env: { ...process.env, LARK_CLI_MCP_PORT: port },
  stdio: ["ignore", "pipe", "pipe"]
});

let client;

try {
  await waitForHealth(port);

  client = new Client({ name: "cli-mcp-server-smoke", version: "0.1.0" });
  const transport = new SSEClientTransport(new URL(`http://127.0.0.1:${port}/sse`));
  await client.connect(transport);

  const tools = await client.listTools();
  const names = tools.tools.map((tool) => tool.name);
  for (const required of ["lark_runtime_status", "lark_profile_list", "lark_skills_list", "lark_docs_fetch", "lark_event_list"]) {
    if (!names.includes(required)) {
      throw new Error(`missing tool ${required}; got ${names.join(", ")}`);
    }
  }

  const runtime = await client.callTool({ name: "lark_runtime_status", arguments: {} });
  const runtimeText = runtime.content?.[0]?.text ?? "";
  if (!runtimeText.includes("scheduler") || !runtimeText.includes("maxConcurrency")) {
    throw new Error(`unexpected lark_runtime_status result: ${runtimeText.slice(0, 500)}`);
  }

  const result = await client.callTool({ name: "lark_skills_list", arguments: {} });
  const text = result.content?.[0]?.text ?? "";
  if (!text.includes("lark-doc") || !text.includes("lark-event")) {
    throw new Error(`unexpected lark_skills_list result: ${text.slice(0, 500)}`);
  }

  console.log(`mcp smoke ok: ${names.length} tools, lark-cli skills reachable`);
} finally {
  await client?.close().catch(() => {});
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
