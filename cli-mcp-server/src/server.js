#!/usr/bin/env node

import { randomUUID, timingSafeEqual } from "node:crypto";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  isInitializeRequest,
  JSONRPCMessageSchema,
  ListToolsRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import { SERVER_NAME, SERVER_VERSION } from "./constants.js";
import { errorContent, getSchedulerStats, shutdownLarkCliScheduler } from "./lark-cli.js";
import { callTool, TOOLS } from "./tools.js";

const DEFAULT_MAX_STREAMABLE_SESSIONS = 128;
const DEFAULT_SESSION_IDLE_TTL_MS = 15 * 60_000;

function createServer() {
  const server = new Server({ name: SERVER_NAME, version: SERVER_VERSION }, { capabilities: { tools: {} } });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;
    try {
      return await callTool(name, args);
    } catch (error) {
      return errorContent(error);
    }
  });
  return server;
}

function verifyBearer(req, res) {
  const expected = process.env.LARK_CLI_MCP_BEARER_TOKEN;
  if (!expected) return true;
  const header = req.get("authorization") ?? "";
  const actual = header.startsWith("Bearer ") ? header.slice("Bearer ".length) : "";
  const expectedBytes = Buffer.from(expected);
  const actualBytes = Buffer.from(actual);
  if (actualBytes.length === expectedBytes.length && timingSafeEqual(actualBytes, expectedBytes)) return true;
  res.status(401).json({ error: "Unauthorized" });
  return false;
}

function isLoopbackHost(host) {
  return host === "127.0.0.1" || host === "::1" || host === "localhost";
}

function main() {
  const port = Number(process.env.PORT ?? process.env.LARK_CLI_MCP_PORT ?? 3000);
  const host = process.env.HOST ?? process.env.LARK_CLI_MCP_HOST ?? "127.0.0.1";
  if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new Error(`invalid MCP port: ${port}`);
  if (!isLoopbackHost(host) && !process.env.LARK_CLI_MCP_BEARER_TOKEN) {
    throw new Error("LARK_CLI_MCP_BEARER_TOKEN is required when binding outside loopback");
  }

  const app = createMcpExpressApp({ host });
  const sseSessions = new Map();
  const streamableSessions = new Map();
  const maxStreamableSessions = positiveIntEnv("LARK_CLI_MCP_MAX_SESSIONS", DEFAULT_MAX_STREAMABLE_SESSIONS);
  const sessionIdleTtlMs = positiveIntEnv("LARK_CLI_MCP_SESSION_IDLE_TTL_MS", DEFAULT_SESSION_IDLE_TTL_MS);

  app.use((error, _req, res, next) => {
    if (error?.type === "entity.parse.failed" || error instanceof SyntaxError) {
      res.status(400).json({ error: "Invalid JSON request" });
      return;
    }
    next(error);
  });

  app.get("/health", (req, res) => {
    if (!verifyBearer(req, res)) return;
    res.json({
      ok: true,
      name: SERVER_NAME,
      version: SERVER_VERSION,
      transports: ["streamable-http", "legacy-sse"],
      scheduler: getSchedulerStats()
    });
  });

  app.all("/mcp", async (req, res) => {
    if (!verifyBearer(req, res)) return;
    if (!["GET", "POST", "DELETE"].includes(req.method)) {
      res.set("allow", "GET, POST, DELETE");
      sendJsonRpcError(res, 405, -32000, "Method not allowed");
      return;
    }

    let session;
    let createdSession = false;
    try {
      const sessionId = req.get("mcp-session-id");
      if (sessionId) {
        session = streamableSessions.get(sessionId);
        if (!session) {
          sendJsonRpcError(res, 404, -32000, "Not Found: unknown MCP session ID");
          return;
        }
        touchSession(session, sessionIdleTtlMs, streamableSessions);
      } else if (req.method === "POST" && isInitializeRequest(req.body)) {
        if (streamableSessions.size >= maxStreamableSessions) {
          sendJsonRpcError(res, 503, -32000, "Server busy: MCP session limit reached");
          return;
        }
        const server = createServer();
        const transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (newSessionId) => {
            streamableSessions.set(newSessionId, session);
          }
        });
        session = { server, transport };
        createdSession = true;
        transport.onclose = () => {
          const closedSessionId = transport.sessionId;
          if (closedSessionId) removeStreamableSession(streamableSessions, closedSessionId);
        };
        await server.connect(transport);
      } else {
        sendJsonRpcError(res, 400, -32000, "Bad Request: missing MCP session ID or initialize request");
        return;
      }

      await session.transport.handleRequest(req, res, req.body);
      if (session.transport.sessionId) touchSession(session, sessionIdleTtlMs, streamableSessions);
      if (req.method === "DELETE") {
        const closedSessionId = session.transport.sessionId ?? sessionId;
        if (closedSessionId) removeStreamableSession(streamableSessions, closedSessionId);
        await closeSession(session);
      }
    } catch (error) {
      if (createdSession && session) {
        const createdSessionId = session.transport.sessionId;
        if (createdSessionId) removeStreamableSession(streamableSessions, createdSessionId);
        await closeSession(session).catch(() => {});
      }
      logServerError("MCP /mcp request failed", error);
      if (!res.headersSent) sendJsonRpcError(res, 500, -32603, "Internal server error");
      else res.end();
    }
  });

  app.get("/sse", async (req, res) => {
    if (!verifyBearer(req, res)) return;
    let session;
    try {
      const server = createServer();
      const transport = new SSEServerTransport("/messages", res, {
        enableDnsRebindingProtection: true,
        allowedHosts: allowedHostHeaders(host, port)
      });
      session = { server, transport };
      sseSessions.set(transport.sessionId, session);
      res.on("close", () => {
        sseSessions.delete(transport.sessionId);
        void server.close().catch(() => {});
      });
      await server.connect(transport);
    } catch (error) {
      logServerError("MCP /sse request failed", error);
      if (session) sseSessions.delete(session.transport.sessionId);
      if (!res.headersSent) res.status(500).json({ error: "Internal server error" });
      else res.end();
    }
  });

  app.post("/messages", async (req, res) => {
    if (!verifyBearer(req, res)) return;
    const sessionId = req.query.sessionId;
    if (typeof sessionId !== "string") {
      res.status(400).json({ error: "Missing sessionId" });
      return;
    }
    const session = sseSessions.get(sessionId);
    if (!session) {
      res.status(404).json({ error: "Unknown sessionId" });
      return;
    }
    try {
      if (!JSONRPCMessageSchema.safeParse(req.body).success) {
        res.status(400).json({ error: "Invalid MCP message" });
        return;
      }
      await session.transport.handlePostMessage(req, res, req.body);
    } catch (error) {
      logServerError("MCP /messages request failed", error);
      if (!res.headersSent) res.status(400).json({ error: "Invalid MCP message" });
      else res.end();
    }
  });

  const httpServer = app.listen(port, host, () => {
    console.error(`${SERVER_NAME} listening on http://${host}:${port}`);
    console.error(`Streamable HTTP endpoint: http://${host}:${port}/mcp`);
    console.error(`SSE endpoint: http://${host}:${port}/sse`);
  });
  httpServer.on("error", (error) => {
    logServerError("MCP HTTP server failed", error);
    process.exitCode = 1;
  });

  let shuttingDown = false;
  const shutdown = async (signal) => {
    if (shuttingDown) return;
    shuttingDown = true;
    console.error(`${SERVER_NAME} received ${signal}; closing sessions and subprocesses`);
    shutdownLarkCliScheduler();
    const sessions = [...streamableSessions.values(), ...sseSessions.values()];
    for (const session of streamableSessions.values()) clearTimeout(session.idleTimer);
    streamableSessions.clear();
    sseSessions.clear();
    await Promise.allSettled(sessions.map(closeSession));
    httpServer.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 2_500).unref();
  };

  process.on("SIGINT", () => void shutdown("SIGINT"));
  process.on("SIGTERM", () => void shutdown("SIGTERM"));
}

async function closeSession(session) {
  clearTimeout(session.idleTimer);
  await session.server.close();
}

function touchSession(session, ttlMs, sessions) {
  clearTimeout(session.idleTimer);
  const sessionId = session.transport.sessionId;
  if (!sessionId) return;
  session.idleTimer = setTimeout(() => {
    if (sessions.get(sessionId) !== session) return;
    sessions.delete(sessionId);
    void closeSession(session).catch(() => {});
  }, ttlMs);
  session.idleTimer.unref();
}

function removeStreamableSession(sessions, sessionId) {
  const session = sessions.get(sessionId);
  if (session) clearTimeout(session.idleTimer);
  sessions.delete(sessionId);
}

function positiveIntEnv(name, fallback) {
  const parsed = Number.parseInt(process.env[name] ?? "", 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

function allowedHostHeaders(host, port) {
  if (host === "::1") return [`[::1]:${port}`, "[::1]"];
  return [`${host}:${port}`, host, `localhost:${port}`, "localhost", `127.0.0.1:${port}`, "127.0.0.1"];
}

function sendJsonRpcError(res, status, code, message) {
  res.status(status).json({ jsonrpc: "2.0", error: { code, message }, id: null });
}

function logServerError(prefix, error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`${prefix}: ${message.replace(/[\r\n\t]+/g, " ").slice(0, 300)}`);
}

main();
