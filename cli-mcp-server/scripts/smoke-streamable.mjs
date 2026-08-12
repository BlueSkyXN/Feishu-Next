import { spawn } from "node:child_process";
import { once } from "node:events";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const port = process.env.LARK_CLI_MCP_PORT ?? "3019";
const child = spawn(process.execPath, ["src/server.js"], {
  cwd: new URL("..", import.meta.url),
  env: { ...process.env, LARK_CLI_MCP_PORT: port, LARK_CLI_MCP_SESSION_IDLE_TTL_MS: "100" },
  stdio: ["ignore", "pipe", "pipe"]
});

let client;

try {
  await waitForHealth(port);

  client = new Client({ name: "cli-mcp-server-streamable-smoke", version: "0.1.0" });
  const transport = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`));
  await client.connect(transport);

  const tools = await client.listTools();
  const names = tools.tools.map((tool) => tool.name);
  for (const required of [
    "lark_auth_login_start",
    "lark_auth_login_complete",
    "lark_runtime_status",
    "lark_profile_list",
    "lark_skills_list",
    "lark_docs_fetch",
    "lark_event_list"
  ]) {
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

  const sessionId = transport.sessionId;
  if (!sessionId) throw new Error("streamable transport did not receive a session ID");
  await new Promise((resolve) => setTimeout(resolve, 200));
  const stale = await fetch(`http://127.0.0.1:${port}/mcp`, {
    method: "POST",
    headers: { "content-type": "application/json", "mcp-session-id": sessionId },
    body: JSON.stringify({ jsonrpc: "2.0", id: 999, method: "ping" })
  });
  if (stale.status !== 404) throw new Error(`expected idle streamable session to expire with 404, got ${stale.status}`);

  const cleanupClient = new Client({ name: "cli-mcp-server-cleanup-smoke", version: "0.1.0" });
  const cleanupTransport = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`));
  await cleanupClient.connect(cleanupTransport);
  const cleanupSessionId = cleanupTransport.sessionId;
  if (!cleanupSessionId) throw new Error("cleanup transport did not receive a session ID");
  await cleanupTransport.terminateSession();
  const deleted = await fetch(`http://127.0.0.1:${port}/mcp`, {
    method: "POST",
    headers: { "content-type": "application/json", "mcp-session-id": cleanupSessionId },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1000, method: "ping" })
  });
  if (deleted.status !== 404) throw new Error(`expected explicitly deleted session to return 404, got ${deleted.status}`);
  await cleanupClient.close().catch(() => {});

  console.log(`streamable smoke ok: ${names.length} tools, idle expiry and explicit session deletion verified`);
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
