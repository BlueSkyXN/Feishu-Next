import { spawn } from "node:child_process";
import { once } from "node:events";
import { chmod, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const port = process.env.LARK_CLI_MCP_PORT ?? "3021";
const profile = "profile-one";
const expectedAppId = "cli_expected123456";
const execution = { context: "system", profile, expectedAppId, identity: "user" };
const tempDir = await mkdtemp(path.join(os.tmpdir(), "lark-cli-mcp-auth-"));
const fakeCli = path.join(tempDir, "lark-cli");
let child;
let client;

try {
  const nonLoopback = spawn(process.execPath, ["src/server.js"], {
    cwd: new URL("..", import.meta.url),
    env: { ...process.env, LARK_CLI_MCP_HOST: "0.0.0.0", LARK_CLI_MCP_PORT: "3023", LARK_CLI_MCP_BEARER_TOKEN: "" },
    stdio: ["ignore", "pipe", "pipe"]
  });
  let nonLoopbackStderr = "";
  nonLoopback.stderr.on("data", (chunk) => {
    nonLoopbackStderr += chunk.toString("utf8");
  });
  const [nonLoopbackExit] = await once(nonLoopback, "close");
  if (nonLoopbackExit === 0 || !nonLoopbackStderr.includes("LARK_CLI_MCP_BEARER_TOKEN is required")) {
    throw new Error(`non-loopback startup guard failed: exit=${nonLoopbackExit}`);
  }

  await writeFile(
    fakeCli,
    [
      "#!/bin/sh",
      `if [ \"$*\" = \"--profile ${profile} config show\" ]; then`,
      `  printf '{\"profile\":\"${profile}\",\"appId\":\"${expectedAppId}\"}\\n'`,
      `elif [ \"$*\" = \"--profile ${profile} whoami --json --as user\" ]; then`,
      `  printf '{\"profile\":\"${profile}\",\"appId\":\"${expectedAppId}\",\"identity\":\"user\",\"available\":true}\\n'`,
      `elif [ \"$*\" = \"--profile ${profile} auth status --json --verify\" ]; then`,
      `  printf '{\"appId\":\"${expectedAppId}\",\"identity\":\"user\",\"verified\":true,\"identities\":{\"user\":{\"available\":true,\"verified\":true}}}\\n'`,
      `elif [ \"$*\" = \"--profile ${profile} auth login --no-wait --json --scope drive:read\" ]; then`,
      "  printf '{\"device_code\":\"DEVICE123\",\"verification_url\":\"https://example.test/verify\",\"user_code\":\"USER123\"}\\n'",
      `elif [ \"$*\" = \"--profile ${profile} auth qrcode https://example.test/verify --ascii\" ]; then`,
      "  printf 'ASCII-QR-CODE\\n'",
      `elif [ \"$*\" = \"--profile ${profile} auth login --device-code DEVICE123 --json\" ]; then`,
      "  printf '{\"ok\":true,\"credential\":\"hidden-value\",\"email\":\"hidden-email-value\"}\\n'",
      "else",
      "  echo \"unexpected lark-cli invocation\" >&2",
      "  exit 2",
      "fi"
    ].join("\n")
  );
  await chmod(fakeCli, 0o755);

  child = spawn(process.execPath, ["src/server.js"], {
    cwd: new URL("..", import.meta.url),
    env: {
      ...process.env,
      PATH: `${tempDir}:${process.env.PATH ?? ""}`,
      LARK_CLI_MCP_PORT: port,
      LARK_CLI_MCP_BEARER_TOKEN: "smoke-auth-token"
    },
    stdio: ["ignore", "pipe", "pipe"]
  });

  await waitForHealth(port, "smoke-auth-token");
  for (const endpoint of ["/health", "/mcp", "/sse", "/messages?sessionId=missing"]) {
    const response = await fetch(`http://127.0.0.1:${port}${endpoint}`, {
      method: endpoint.startsWith("/messages") ? "POST" : "GET",
      headers: endpoint.startsWith("/messages") ? { "content-type": "application/json" } : undefined,
      body: endpoint.startsWith("/messages") ? "{}" : undefined
    });
    if (response.status !== 401) throw new Error(`expected ${endpoint} without bearer to return 401, got ${response.status}`);
  }

  const invalidJson = await fetch(`http://127.0.0.1:${port}/messages?sessionId=missing`, {
    method: "POST",
    headers: { authorization: "Bearer smoke-auth-token", "content-type": "application/json" },
    body: "{PRIVATE_INVALID_BODY"
  });
  const invalidJsonText = await invalidJson.text();
  if (invalidJson.status !== 400 || invalidJsonText.includes("PRIVATE_INVALID_BODY")) {
    throw new Error(`invalid JSON was not rejected generically: ${invalidJson.status} ${invalidJsonText}`);
  }

  const unknownSession = await fetch(`http://127.0.0.1:${port}/messages?sessionId=missing`, {
    method: "POST",
    headers: { authorization: "Bearer smoke-auth-token", "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" })
  });
  if (unknownSession.status !== 404) throw new Error(`expected unknown legacy session to return 404, got ${unknownSession.status}`);

  const rebinding = await requestWithHost(port, "attacker.example");
  if (rebinding.status !== 403) throw new Error(`expected invalid Host to return 403, got ${rebinding.status}`);

  client = new Client({ name: "cli-mcp-server-auth-smoke", version: "0.1.0" });
  const transport = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`), {
    requestInit: { headers: { authorization: "Bearer smoke-auth-token" } }
  });
  await client.connect(transport);

  const start = await client.callTool({
    name: "lark_auth_login_start",
    arguments: { ...execution, scope: "drive:read", asciiQr: true }
  });
  const startText = start.content?.[0]?.text ?? "";
  for (const required of ["https://example.test/verify", "USER123", "ASCII-QR-CODE", "authorizationHandle"]) {
    if (!startText.includes(required)) throw new Error(`login start missing ${required}: ${startText}`);
  }
  if (startText.includes("DEVICE123")) throw new Error(`login start leaked device code: ${startText}`);
  const authorizationHandle = JSON.parse(startText).authorizationHandle;

  const complete = await client.callTool({
    name: "lark_auth_login_complete",
    arguments: { ...execution, authorizationHandle }
  });
  const completeText = complete.content?.[0]?.text ?? "";
  for (const forbidden of ["hidden-value", "hidden-email-value", "DEVICE123"]) {
    if (completeText.includes(forbidden)) throw new Error(`login complete leaked ${forbidden}: ${completeText}`);
  }

  const replay = await client.callTool({
    name: "lark_auth_login_complete",
    arguments: { ...execution, authorizationHandle }
  });
  if (!replay.isError || !(replay.content?.[0]?.text ?? "").includes("invalid or expired")) {
    throw new Error(`expected handle replay rejection: ${JSON.stringify(replay)}`);
  }

  console.log("auth smoke ok: bearer/Host guards, execution preflight, opaque one-time OAuth handle, and redaction verified");
} finally {
  await client?.close().catch(() => {});
  if (child) {
    child.kill("SIGTERM");
    await once(child, "close").catch(() => {});
  }
  await rm(tempDir, { recursive: true, force: true });
}

async function waitForHealth(portValue, token) {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${portValue}/health`, {
        headers: { authorization: `Bearer ${token}` }
      });
      if (response.ok) return;
    } catch {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error("server did not become healthy");
}

async function requestWithHost(portValue, hostHeader) {
  const http = await import("node:http");
  return await new Promise((resolve, reject) => {
    const request = http.request(
      {
        hostname: "127.0.0.1",
        port: portValue,
        path: "/health",
        headers: { authorization: "Bearer smoke-auth-token", host: hostHeader }
      },
      (response) => {
        response.resume();
        response.on("end", () => resolve({ status: response.statusCode }));
      }
    );
    request.on("error", reject);
    request.end();
  });
}
