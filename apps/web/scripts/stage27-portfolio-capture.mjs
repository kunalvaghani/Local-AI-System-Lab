import { mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const webRoot = fileURLToPath(new URL("../", import.meta.url));
const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));
const browserCli = path.join(webRoot, "node_modules", "agent-browser", "bin", "agent-browser.js");
const baseUrl = process.env.PORTFOLIO_WEB_BASE ?? "http://127.0.0.1:4173";
const outputDirectory = process.env.PORTFOLIO_CAPTURE_DIRECTORY
  ?? path.join(repositoryRoot, "docs", "assets", "portfolio");
const session = process.env.PORTFOLIO_BROWSER_SESSION ?? `stage27-${process.pid}`;

mkdirSync(outputDirectory, { recursive: true });

function run(args, { input, tolerate = false } = {}) {
  const result = spawnSync(process.execPath, [browserCli, "--session", session, ...args], {
    cwd: webRoot,
    encoding: "utf8",
    input,
    timeout: 45_000,
    windowsHide: true,
  });
  if (!tolerate && result.status !== 0) {
    throw new Error(`agent-browser ${args.join(" ")} failed: ${result.stderr || result.stdout}`);
  }
  return (result.stdout || result.stderr || "").trim();
}

function value(expression) {
  const output = run(["eval", "--stdin"], { input: expression });
  return JSON.parse(output.split(/\r?\n/).filter(Boolean).at(-1) ?? "null");
}

async function waitFor(expression, label, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (value(expression) === true) return;
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`portfolio capture timed out: ${label}`);
}

function contains(text) {
  return `document.body.innerText.includes(${JSON.stringify(text)})`;
}

function screenshot(name) {
  const target = path.join(outputDirectory, name);
  run(["screenshot", "--full", target]);
  return target;
}

function assertNoRuntimeError(label) {
  const runtimeError = value("document.querySelector('.runtime-error')?.textContent?.trim() || ''");
  if (!runtimeError) return;
  const failedRequests = run(["network", "requests", "--status", "400-499", "--json"], { tolerate: true });
  throw new Error(`${label} is not release-ready: ${runtimeError}\n${failedRequests}`);
}

const captures = [];
let taskId = null;

try {
  run(["set", "viewport", "1440", "900"]);
  run(["open", `${baseUrl}/runtime`]);
  run(["wait", "--load", "networkidle"]);
  await waitFor(contains("Runtime live"), "runtime health");
  await waitFor("document.querySelector('.tool-probe select') !== null", "tool catalog");
  assertNoRuntimeError("runtime page");
  run(["find", "label", "Objective", "fill", "Capture the verified local runtime product story."]);
  run(["find", "role", "button", "click", "--name", "Launch task"]);
  await waitFor("window.location.search.includes('task=')", "selected task URL");
  taskId = value("new URLSearchParams(window.location.search).get('task')");
  await waitFor(contains("completed"), "task completion");
  assertNoRuntimeError("completed runtime page");
  captures.push(screenshot("runtime-command-center.png"));

  run(["open", `${baseUrl}/scheduler?task=${encodeURIComponent(taskId)}`]);
  await waitFor(contains("Scheduler map"), "scheduler view");
  assertNoRuntimeError("scheduler page");
  captures.push(screenshot("scheduler-execution.png"));

  run(["open", `${baseUrl}/traces?task=${encodeURIComponent(taskId)}`]);
  await waitFor(contains("Trace explorer"), "trace view");
  run(["find", "role", "button", "click", "--name", "Replay deterministic reducers"]);
  await waitFor(contains("Valid"), "valid replay");
  assertNoRuntimeError("trace page");
  captures.push(screenshot("trace-replay-debugger.png"));

  run(["open", `${baseUrl}/hardware?task=${encodeURIComponent(taskId)}`]);
  await waitFor(contains("Hardware & performance lab"), "hardware view");
  await waitFor("!document.body.innerText.includes('Collecting')", "hardware measurements");
  assertNoRuntimeError("hardware page");
  captures.push(screenshot("hardware-performance-lab.png"));

  run(["open", `${baseUrl}/security`]);
  await waitFor(contains("Security lab"), "security view");
  assertNoRuntimeError("security page");
  captures.push(screenshot("chaos-security-lab.png"));

  const overlayCount = value("document.querySelectorAll('.vite-error-overlay, #webpack-dev-server-client-overlay').length");
  if (overlayCount !== 0) throw new Error("a development error overlay is visible");
  console.log(JSON.stringify({ base_url: baseUrl, captures, task_id: taskId, viewport: { width: 1440, height: 900 } }));
} finally {
  run(["close"], { tolerate: true });
}
