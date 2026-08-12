import http from "node:http";
import { spawn } from "node:child_process";
import { once } from "node:events";

const port = process.env.LARK_CLI_MCP_PORT ?? "3022";
const child = spawn(process.execPath, ["src/server.js"], {
  cwd: new URL("..", import.meta.url),
  env: { ...process.env, LARK_CLI_MCP_PORT: port },
  stdio: ["ignore", "pipe", "pipe"]
});

try {
  await waitForHealth(port);
  const legacy = await openLegacySession(port);
  const sessionId = legacy.sessionId;

  const invalid = await request({
    port,
    path: `/messages?sessionId=${encodeURIComponent(sessionId)}`,
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ private: "PRIVATE_LEGACY_BODY" })
  });
  if (invalid.status !== 400 || invalid.body.includes("PRIVATE_LEGACY_BODY")) {
    throw new Error(`legacy invalid body was not rejected generically: ${JSON.stringify(invalid)}`);
  }

  legacy.close();
  await waitForUnknownSession(port, sessionId);
  const unknown = await request({
    port,
    path: "/messages?sessionId=missing",
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" })
  });
  if (unknown.status !== 404 || unknown.body.includes("ping")) {
    throw new Error(`unknown session handling failed: ${JSON.stringify(unknown)}`);
  }

  console.log("transport smoke ok: legacy invalid-body redaction and disconnect cleanup verified");
} finally {
  child.kill("SIGTERM");
  await once(child, "close").catch(() => {});
}

async function openLegacySession(portValue) {
  return await new Promise((resolve, reject) => {
    const requestHandle = http.get(`http://127.0.0.1:${portValue}/sse`, (response) => {
      response.setEncoding("utf8");
      let data = "";
      response.on("data", (chunk) => {
        data += chunk;
        const match = data.match(/sessionId=([0-9a-f-]{36})/i);
        if (!match) return;
        resolve({ sessionId: match[1], close: () => response.destroy() });
      });
      response.on("error", () => {});
    });
    requestHandle.on("error", reject);
  });
}

async function waitForUnknownSession(portValue, sessionId) {
  const deadline = Date.now() + 5_000;
  while (Date.now() < deadline) {
    const response = await request({
      port: portValue,
      path: `/messages?sessionId=${encodeURIComponent(sessionId)}`,
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "ping" })
    });
    if (response.status === 404) return;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("legacy session remained registered after SSE disconnect");
}

async function waitForHealth(portValue) {
  const deadline = Date.now() + 10_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${portValue}/health`);
      if (response.ok) return;
    } catch {
      // retry
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error("server did not become healthy");
}

async function request({ port: portValue, path, method, headers, body }) {
  return await new Promise((resolve, reject) => {
    const requestHandle = http.request(
      { hostname: "127.0.0.1", port: portValue, path, method, headers },
      (response) => {
        response.setEncoding("utf8");
        let responseBody = "";
        response.on("data", (chunk) => {
          responseBody += chunk;
        });
        response.on("end", () => resolve({ status: response.statusCode, body: responseBody }));
      }
    );
    requestHandle.on("error", reject);
    requestHandle.end(body);
  });
}
