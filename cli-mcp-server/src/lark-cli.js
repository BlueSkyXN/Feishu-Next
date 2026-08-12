import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";

const DEFAULT_TIMEOUT_MS = 120_000;
const DEFAULT_OUTPUT_LIMIT = 8 * 1024 * 1024;
const DEFAULT_MAX_CONCURRENCY = 4;
const DEFAULT_MAX_QUEUE = 64;
const DEFAULT_TERMINATION_GRACE_MS = 2_000;

let activeRuns = 0;
let completedRuns = 0;
const pendingRuns = [];
const activeChildren = new Set();
let schedulerShuttingDown = false;

export class LarkCliError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "LarkCliError";
    this.details = details;
  }
}

export function parseJsonMaybe(text) {
  const trimmed = String(text ?? "").trim();
  if (!trimmed) return undefined;
  try {
    return JSON.parse(trimmed);
  } catch {
    return undefined;
  }
}

export function parseJsonLines(text) {
  const rows = [];
  for (const line of String(text ?? "").split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const parsed = parseJsonMaybe(trimmed);
    rows.push(parsed ?? { text: trimmed });
  }
  return rows;
}

export function isSafeRelativePath(value) {
  if (typeof value !== "string" || value.length === 0) return false;
  if (value.startsWith("/") || value.startsWith("~")) return false;
  if (value.includes("\0")) return false;
  const parts = value.split(/[\\/]+/);
  return !parts.includes("..");
}

export function buildParams(params = {}) {
  return Object.entries(params).flatMap(([key, value]) => {
    if (value === undefined || value === null || value === "") return [];
    return ["--param", `${key}=${value}`];
  });
}

export function redactAuthStatus(payload) {
  if (!payload || typeof payload !== "object") return payload;
  const clone = structuredClone(payload);
  if (clone.appId) clone.appId = redactIdentifier(clone.appId);
  for (const identity of Object.values(clone.identities ?? {})) {
    if (identity && typeof identity === "object") {
      delete identity.openId;
      delete identity.userName;
      delete identity.scope;
      delete identity.expiresAt;
      delete identity.refreshExpiresAt;
      delete identity.grantedAt;
    }
  }
  return clone;
}

export function redactSensitivePayload(payload) {
  return redactValue(payload);
}

function redactValue(value, key = "") {
  if (Array.isArray(value)) {
    return value.map((item) => redactValue(item));
  }
  if (!value || typeof value !== "object") {
    if (isSensitiveKey(key)) return "***";
    return value;
  }

  const clone = {};
  for (const [childKey, childValue] of Object.entries(value)) {
    if (isSensitiveKey(childKey)) {
      clone[childKey] = "***";
    } else if (isIdentityDetailKey(childKey)) {
      continue;
    } else if (childKey === "appId") {
      clone[childKey] = redactIdentifier(childValue);
    } else {
      clone[childKey] = redactValue(childValue, childKey);
    }
  }
  return clone;
}

function isSensitiveKey(key) {
  return /token|secret|cookie|authorization|credential|session|device.?code|user.?code|verification|oauth.?state/i.test(
    String(key)
  );
}

function isIdentityDetailKey(key) {
  return ["openId", "unionId", "userId", "userName", "email", "scope", "expiresAt", "refreshExpiresAt", "grantedAt"].includes(
    key
  );
}

export function redactIdentifier(value) {
  const text = String(value ?? "");
  if (text.length <= 10) return "***";
  return `${text.slice(0, 6)}...${text.slice(-4)}`;
}

export function getSchedulerStats() {
  const config = getSchedulerConfig();
  return {
    activeRuns,
    pendingRuns: pendingRuns.length,
    completedRuns,
    maxConcurrency: config.maxConcurrency,
    maxQueue: config.maxQueue
  };
}

export async function runLarkCli(args, options = {}) {
  if (!Array.isArray(args) || args.some((arg) => typeof arg !== "string")) {
    throw new TypeError("args must be an array of strings");
  }

  return await enqueueRun(args, options);
}

export function shutdownLarkCliScheduler() {
  schedulerShuttingDown = true;
  while (pendingRuns.length > 0) {
    const job = pendingRuns.shift();
    job.resolve(failedResult(job.options.requestId, "scheduler_shutdown", "lark-cli scheduler is shutting down"));
  }
  for (const child of activeChildren) {
    child._larkCliMcpForceKill?.(false);
  }
}

function getSchedulerConfig() {
  return {
    maxConcurrency: positiveIntEnv("LARK_CLI_MCP_MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY),
    maxQueue: positiveIntEnv("LARK_CLI_MCP_MAX_QUEUE", DEFAULT_MAX_QUEUE)
  };
}

function positiveIntEnv(name, fallback) {
  const parsed = Number.parseInt(process.env[name] ?? "", 10);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

async function enqueueRun(args, options) {
  const requestId = options.requestId ?? randomUUID();
  const config = getSchedulerConfig();

  if (schedulerShuttingDown) {
    return failedResult(requestId, "scheduler_shutdown", "lark-cli scheduler is shutting down");
  }

  if (activeRuns >= config.maxConcurrency && pendingRuns.length >= config.maxQueue) {
    return failedResult(
      requestId,
      "queue_full",
      `lark-cli scheduler queue is full (${pendingRuns.length}/${config.maxQueue})`
    );
  }

  return await new Promise((resolve) => {
    pendingRuns.push({ args, options: { ...options, requestId }, resolve });
    drainQueue();
  });
}

function drainQueue() {
  const { maxConcurrency } = getSchedulerConfig();
  while (activeRuns < maxConcurrency && pendingRuns.length > 0) {
    const job = pendingRuns.shift();
    activeRuns += 1;
    runLarkCliProcess(job.args, job.options)
      .then(job.resolve)
      .catch((error) => {
        job.resolve(
          failedResult(
            job.options.requestId,
            "scheduler_error",
            error instanceof Error ? error.message : String(error)
          )
        );
      })
      .finally(() => {
        activeRuns -= 1;
        completedRuns += 1;
        drainQueue();
      });
  }
}

async function runLarkCliProcess(args, options = {}) {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const outputLimit = options.outputLimit ?? DEFAULT_OUTPUT_LIMIT;
  const requestId = options.requestId ?? randomUUID();
  const startedAt = Date.now();

  return await new Promise((resolve) => {
    const child = spawn("lark-cli", args, {
      cwd: options.cwd ?? process.cwd(),
      env: {
        ...process.env,
        LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1",
        LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1"
      },
      shell: false,
      stdio: ["pipe", "pipe", "pipe"]
    });
    activeChildren.add(child);

    let stdout = "";
    let stderr = "";
    let truncated = false;
    let killedByTimeout = false;
    let settled = false;
    let terminationTimer;

    const append = (current, chunk) => {
      if (current.length >= outputLimit) {
        truncated = true;
        return current;
      }
      const next = current + chunk.toString("utf8");
      if (next.length > outputLimit) {
        truncated = true;
        return next.slice(0, outputLimit);
      }
      return next;
    };

    const timeoutTimer = setTimeout(() => {
      child._larkCliMcpForceKill?.(true);
    }, timeoutMs);
    timeoutTimer.unref();

    const settle = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeoutTimer);
      clearTimeout(terminationTimer);
      activeChildren.delete(child);
      delete child._larkCliMcpForceKill;
      resolve(result);
    };

    child._larkCliMcpForceKill = (isTimeout) => {
      if (isTimeout) killedByTimeout = true;
      child.kill("SIGTERM");
      if (terminationTimer) return;
      terminationTimer = setTimeout(() => {
        if (child.exitCode === null && child.signalCode === null) child.kill("SIGKILL");
      }, options.terminationGraceMs ?? DEFAULT_TERMINATION_GRACE_MS);
      terminationTimer.unref();
    };

    child.stdout.on("data", (chunk) => {
      stdout = append(stdout, chunk);
    });

    child.stderr.on("data", (chunk) => {
      stderr = append(stderr, chunk);
    });

    child.on("error", (error) => {
      settle({
        requestId,
        ok: false,
        exitCode: null,
        signal: null,
        stdout,
        stderr,
        parsedStdout: undefined,
        parsedStderr: undefined,
        durationMs: Date.now() - startedAt,
        truncated,
        error: {
          type: "spawn_error",
          message: error.message
        }
      });
    });

    child.on("close", (exitCode, signal) => {
      const parsedStdout = parseJsonMaybe(stdout);
      const parsedStderr = parseJsonMaybe(stderr);
      const envelopeError = parsedStderr?.error ?? parsedStdout?.error;
      settle({
        requestId,
        ok: exitCode === 0 && !envelopeError,
        exitCode,
        signal,
        stdout,
        stderr,
        parsedStdout,
        parsedStderr,
        durationMs: Date.now() - startedAt,
        truncated,
        error: killedByTimeout
          ? { type: "timeout", message: `lark-cli timed out after ${timeoutMs}ms` }
          : envelopeError
      });
    });

    child.stdin.end();
  });
}

export function requireSuccess(result) {
  if (result.ok) return result;

  const message =
    result.error?.message ??
    result.parsedStderr?.error?.message ??
    result.parsedStdout?.error?.message ??
    firstNonEmptyLine(result.stderr) ??
    `lark-cli exited with code ${result.exitCode}`;

  throw new LarkCliError(message, result);
}

export function resultContent(result, transform = (value) => value) {
  const payload = result.parsedStdout ?? parseJsonLines(result.stdout);
  const structured = transform(payload);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(structured, null, 2)
      }
    ],
    structuredContent: structured
  };
}

export function errorContent(error) {
  const details = error instanceof LarkCliError ? error.details : {};
  const rawError = details.error ?? details.parsedStderr?.error ?? details.parsedStdout?.error;
  const message =
    error instanceof LarkCliError
      ? "lark-cli operation failed; use the request ID for local diagnostics"
      : sanitizeErrorMessage(error instanceof Error ? error.message : String(error));
  const envelope = {
    error: {
      type: sanitizeErrorType(rawError?.type ?? (error instanceof LarkCliError ? "lark_cli_error" : "tool_error")),
      message
    }
  };
  if (Number.isInteger(details.exitCode)) envelope.error.exitCode = details.exitCode;
  if (typeof details.signal === "string" && details.signal) envelope.error.signal = details.signal;
  if (typeof details.requestId === "string") envelope.error.requestId = details.requestId;
  if (details.truncated === true) envelope.error.truncated = true;
  return {
    isError: true,
    content: [
      {
        type: "text",
        text: JSON.stringify(envelope, null, 2)
      }
    ],
    structuredContent: envelope
  };
}

function failedResult(requestId, type, message) {
  return {
    requestId,
    ok: false,
    exitCode: null,
    signal: null,
    stdout: "",
    stderr: "",
    parsedStdout: undefined,
    parsedStderr: undefined,
    durationMs: 0,
    truncated: false,
    error: { type, message }
  };
}

function firstNonEmptyLine(value) {
  const line = String(value ?? "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .find(Boolean);
  return line || undefined;
}

function sanitizeErrorType(value) {
  const type = String(value ?? "tool_error").toLowerCase();
  return /^[a-z0-9_-]{1,64}$/.test(type) ? type : "tool_error";
}

function sanitizeErrorMessage(value) {
  let message = String(value ?? "operation failed").replace(/[\r\n\t]+/g, " ").trim();
  message = message.replace(/https?:\/\/\S+/gi, "[redacted-url]");
  message = message.replace(/\b(?:cli|app)_[a-z0-9]{8,}\b/gi, "[redacted-id]");
  message = message.replace(
    /\b(device[_ -]?code|authorization|bearer|token|secret|cookie|session)\s*[:=]\s*\S+/gi,
    "$1=[redacted]"
  );
  message = message.replace(/\b--device-code\s+\S+/gi, "--device-code [redacted]");
  if (message.length > 300) message = `${message.slice(0, 300)}...`;
  return message || "operation failed";
}
