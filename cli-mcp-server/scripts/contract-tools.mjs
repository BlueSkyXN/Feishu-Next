import assert from "node:assert/strict";
import { createToolCaller, TOOLS } from "../src/tools.js";
import { errorContent, LarkCliError } from "../src/lark-cli.js";

const expectedTools = [
  "lark_auth_status",
  "lark_auth_login_start",
  "lark_auth_login_complete",
  "lark_doctor_offline",
  "lark_runtime_status",
  "lark_profile_list",
  "lark_skills_list",
  "lark_skill_read",
  "lark_event_list",
  "lark_event_schema",
  "lark_drive_inspect",
  "lark_drive_search",
  "lark_docs_fetch",
  "lark_event_consume_bounded",
  "lark_api_dry_run"
];

assert.deepEqual(TOOLS.map((tool) => tool.name), expectedTools);
for (const tool of TOOLS) {
  assert.equal(tool.inputSchema.type, "object", `${tool.name} must use object input schema`);
  assert.equal(tool.inputSchema.additionalProperties, false, `${tool.name} must reject unknown top-level args`);
}

const execution = {
  context: "system",
  profile: "profile-one",
  expectedAppId: "cli_expected123456",
  identity: "user"
};
const calls = [];
let clock = 1_000;
const callTool = createToolCaller({
  now: () => clock,
  run: async (args, options = {}) => {
    calls.push({ args, options });
    if (matches(args, ["--profile", execution.profile, "config", "show"])) {
      return ok({ profile: execution.profile, appId: execution.expectedAppId });
    }
    if (matches(args, ["--profile", execution.profile, "whoami", "--json", "--as", execution.identity])) {
      return ok({
        profile: execution.profile,
        appId: execution.expectedAppId,
        identity: execution.identity,
        available: true,
        tokenStatus: "ready"
      });
    }
    if (matches(args, ["--profile", execution.profile, "auth", "status", "--json", "--verify"])) {
      return ok({
        appId: execution.expectedAppId,
        identity: execution.identity,
        verified: true,
        identities: { user: { available: true, verified: true, openId: "hidden-open-id" } }
      });
    }
    if (args.includes("--no-wait")) {
      return ok({ device_code: "DEVICE123", verification_url: "https://example.test/verify", user_code: "USER123" });
    }
    if (args.includes("qrcode")) return okText("ASCII-QR\n");
    if (args.includes("--device-code")) return ok({ credential: "hidden-value", email: "hidden-email-value" });
    if (args.includes("consume")) return okText('{"ok":true}\n');
    return ok({ ok: true, argv: args });
  },
  schedulerStats: () => ({ activeRuns: 0, pendingRuns: 0, completedRuns: 0, maxConcurrency: 4, maxQueue: 64 })
});

await callTool("lark_runtime_status", {});
assert.deepEqual(calls.splice(0), []);

await callTool("lark_profile_list", {});
assert.deepEqual(calls.splice(0)[0].args, ["profile", "list"]);

await callTool("lark_event_schema", { key: "im.message.receive_v1" });
assert.deepEqual(calls.splice(0)[0].args, ["event", "schema", "im.message.receive_v1", "--json"]);

const start = await callTool("lark_auth_login_start", {
  ...execution,
  scope: "drive:read",
  domain: ["drive", "docs"],
  recommend: true,
  exclude: ["x", "y"],
  asciiQr: true
});
const startText = start.content[0].text;
assert.ok(!startText.includes("DEVICE123"), "login start must not expose device code");
assert.ok(startText.includes("https://example.test/verify"), "login start must return verification URL");
assert.ok(startText.includes("USER123"), "login start must return user code");
assert.ok(startText.includes("ASCII-QR"), "login start must return requested ASCII QR");
const authorizationHandle = start.structuredContent.authorizationHandle;
assert.match(authorizationHandle, /^[0-9a-f-]{36}$/);
const startCalls = calls.splice(0);
assertPreflight(startCalls.slice(0, 3));
assert.deepEqual(startCalls[3].args, [
  "--profile",
  execution.profile,
  "auth",
  "login",
  "--no-wait",
  "--json",
  "--scope",
  "drive:read",
  "--domain",
  "drive",
  "--domain",
  "docs",
  "--recommend",
  "--exclude",
  "x",
  "--exclude",
  "y"
]);
assert.deepEqual(startCalls[4].args, [
  "--profile",
  execution.profile,
  "auth",
  "qrcode",
  "https://example.test/verify",
  "--ascii"
]);

const complete = await callTool("lark_auth_login_complete", { ...execution, authorizationHandle });
assert.ok(!complete.content[0].text.includes("hidden-value"));
assert.ok(!complete.content[0].text.includes("hidden-email-value"));
const completeCalls = calls.splice(0);
assertPreflight(completeCalls.slice(0, 3));
assert.deepEqual(completeCalls[3], {
  args: ["--profile", execution.profile, "auth", "login", "--device-code", "DEVICE123", "--json"],
  options: { timeoutMs: 180_000 }
});
await assert.rejects(
  () => callTool("lark_auth_login_complete", { ...execution, authorizationHandle }),
  /invalid or expired/
);
calls.splice(0);

await callTool("lark_drive_inspect", { ...execution, url: "https://example.test/doc", type: "docx" });
const inspectCalls = calls.splice(0);
assertPreflight(inspectCalls.slice(0, 3));
assert.deepEqual(inspectCalls[3].args, [
  "--profile",
  execution.profile,
  "drive",
  "+inspect",
  "--json",
  "--url",
  "https://example.test/doc",
  "--type",
  "docx",
  "--as",
  "user"
]);

await callTool("lark_docs_fetch", {
  ...execution,
  doc: "DOC_TOKEN",
  scope: "keyword",
  detail: "full",
  docFormat: "markdown",
  keyword: "hello",
  startBlockId: "start",
  endBlockId: "end",
  maxDepth: 3
});
const docsCalls = calls.splice(0);
assertPreflight(docsCalls.slice(0, 3));
assert.deepEqual(docsCalls[3].args, [
  "--profile",
  execution.profile,
  "docs",
  "+fetch",
  "--json",
  "--doc",
  "DOC_TOKEN",
  "--scope",
  "keyword",
  "--detail",
  "full",
  "--doc-format",
  "markdown",
  "--keyword",
  "hello",
  "--start-block-id",
  "start",
  "--end-block-id",
  "end",
  "--max-depth",
  "3",
  "--as",
  "user"
]);

await callTool("lark_event_consume_bounded", {
  ...execution,
  key: "im.message.receive_v1",
  maxEvents: 2,
  timeout: "3s",
  params: { chat_id: "CHAT" },
  jq: "."
});
const eventCalls = calls.splice(0);
assertPreflight(eventCalls.slice(0, 3));
assert.deepEqual(eventCalls[3].options, { timeoutMs: 18_000 });
assert.ok(!eventCalls[3].args.includes("auto"), "event identity must remain frozen");

await callTool("lark_api_dry_run", {
  ...execution,
  method: "POST",
  path: "/open-apis/example/v1/items",
  params: { q: "--yes" },
  data: { nested: ["--yes"] }
});
const apiCalls = calls.splice(0);
assertPreflight(apiCalls.slice(0, 3));
assert.ok(apiCalls[3].args.includes("--dry-run"), "raw API wrapper must stay dry-run only");
assert.equal(apiCalls[3].args.filter((arg) => arg === "--yes").length, 0);

const error = errorContent(
  new LarkCliError("request failed at https://private.example/doc device_code=DEVICE123", {
    requestId: "request-1",
    args: ["auth", "login", "--device-code", "DEVICE123"],
    stdout: "private document body",
    stderr: "private stderr",
    exitCode: 7,
    error: { type: "authorization" }
  })
);
const errorText = error.content[0].text;
for (const forbidden of ["DEVICE123", "private.example", "private document body", "private stderr", "request failed", '"args"']) {
  assert.ok(!errorText.includes(forbidden), `error envelope leaked ${forbidden}`);
}
assert.ok(errorText.includes("request-1"));
assert.ok(errorText.includes('"exitCode": 7'));

await assert.rejects(() => callTool("lark_drive_search", { pageSize: 21 }), /required/);
await assert.rejects(() => callTool("lark_event_schema", { key: "--help" }), /invalid format/);
await assert.rejects(() => callTool("lark_docs_fetch", { ...execution, doc: "--profile" }), /invalid format/);
await assert.rejects(() => callTool("lark_drive_inspect", { ...execution, url: "--yes" }), /invalid format/);
await assert.rejects(() => callTool("lark_api_dry_run", { ...execution, method: "TRACE", path: "/open-apis/example" }), /allowed value/);
await assert.rejects(() => callTool("lark_api_dry_run", { ...execution, method: "GET", path: "https://example.test" }), /invalid format/);
await assert.rejects(() => callTool("lark_docs_fetch", { ...execution, doc: "x", extra: true }), /not allowed/);
await assert.rejects(() => callTool("lark_unknown", {}), /Unknown tool/);

const previousChannel = process.env.LARK_CHANNEL;
process.env.LARK_CHANNEL = "1";
await assert.rejects(
  () => callTool("lark_auth_status", execution),
  /execution_context_mismatch/
);
if (previousChannel === undefined) delete process.env.LARK_CHANNEL;
else process.env.LARK_CHANNEL = previousChannel;
assert.deepEqual(calls.splice(0), []);

clock += 11 * 60_000;
console.log("tool contract ok: execution preflight, opaque OAuth handle, argv mapping, and redaction verified");

function assertPreflight(entries) {
  assert.deepEqual(entries.map((entry) => entry.args), [
    ["--profile", execution.profile, "config", "show"],
    ["--profile", execution.profile, "whoami", "--json", "--as", execution.identity],
    ["--profile", execution.profile, "auth", "status", "--json", "--verify"]
  ]);
}

function matches(left, right) {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function ok(parsedStdout) {
  return {
    requestId: "test",
    ok: true,
    exitCode: 0,
    signal: null,
    stdout: JSON.stringify(parsedStdout),
    stderr: "",
    parsedStdout,
    parsedStderr: undefined,
    durationMs: 1,
    truncated: false
  };
}

function okText(stdout) {
  return {
    requestId: "test",
    ok: true,
    exitCode: 0,
    signal: null,
    stdout,
    stderr: "",
    parsedStdout: undefined,
    parsedStderr: undefined,
    durationMs: 1,
    truncated: false
  };
}
