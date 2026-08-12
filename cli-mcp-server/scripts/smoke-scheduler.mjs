import { chmod, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const tempDir = await mkdtemp(path.join(os.tmpdir(), "lark-cli-mcp-scheduler-"));
const fakeCli = path.join(tempDir, "lark-cli");

try {
  await writeFile(
    fakeCli,
    [
      "#!/bin/sh",
      "sleep 0.25",
      "printf '{\"ok\":true,\"argv\":\"%s\"}\\n' \"$*\""
    ].join("\n")
  );
  await chmod(fakeCli, 0o755);

  process.env.PATH = `${tempDir}:${process.env.PATH ?? ""}`;
  process.env.LARK_CLI_MCP_MAX_CONCURRENCY = "1";
  process.env.LARK_CLI_MCP_MAX_QUEUE = "1";

  const { getSchedulerStats, runLarkCli } = await import("../src/lark-cli.js");

  const first = runLarkCli(["first"]);
  await sleep(30);
  const second = runLarkCli(["second"]);
  await sleep(30);
  const third = runLarkCli(["third"]);

  const queued = getSchedulerStats();
  if (queued.maxConcurrency !== 1 || queued.maxQueue !== 1) {
    throw new Error(`unexpected scheduler config: ${JSON.stringify(queued)}`);
  }
  if (queued.activeRuns !== 1 || queued.pendingRuns !== 1) {
    throw new Error(`expected one active and one pending run: ${JSON.stringify(queued)}`);
  }

  const [firstResult, secondResult, thirdResult] = await Promise.all([first, second, third]);
  if (!firstResult.ok || !secondResult.ok) {
    throw new Error(`expected first two runs to succeed: ${JSON.stringify([firstResult, secondResult])}`);
  }
  if (thirdResult.ok || thirdResult.error?.type !== "queue_full") {
    throw new Error(`expected third run to be rejected by scheduler: ${JSON.stringify(thirdResult)}`);
  }

  const finalStats = getSchedulerStats();
  if (finalStats.activeRuns !== 0 || finalStats.pendingRuns !== 0 || finalStats.completedRuns !== 2) {
    throw new Error(`unexpected final scheduler stats: ${JSON.stringify(finalStats)}`);
  }

  await writeFile(
    fakeCli,
    [
      "#!/bin/sh",
      "trap '' TERM",
      "while :; do sleep 1; done"
    ].join("\n")
  );
  await chmod(fakeCli, 0o755);
  const timedOut = await runLarkCli(["ignore-term"], { timeoutMs: 50, terminationGraceMs: 50 });
  if (timedOut.ok || timedOut.error?.type !== "timeout" || timedOut.signal !== "SIGKILL") {
    throw new Error(`expected SIGKILL timeout convergence: ${JSON.stringify(timedOut)}`);
  }
  const afterTimeout = getSchedulerStats();
  if (afterTimeout.activeRuns !== 0 || afterTimeout.pendingRuns !== 0 || afterTimeout.completedRuns !== 3) {
    throw new Error(`scheduler slot did not recover after forced timeout: ${JSON.stringify(afterTimeout)}`);
  }

  console.log("scheduler smoke ok: bounded queue and SIGTERM-to-SIGKILL timeout convergence verified");
} finally {
  await rm(tempDir, { recursive: true, force: true });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
