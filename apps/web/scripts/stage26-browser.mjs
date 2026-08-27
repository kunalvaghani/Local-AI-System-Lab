import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const webRoot = fileURLToPath(new URL("../", import.meta.url));
const browserCli = path.join(webRoot, "node_modules", "agent-browser", "bin", "agent-browser.js");
const baseUrl = process.env.STAGE26_WEB_BASE ?? "http://127.0.0.1:4173";
const session = process.env.STAGE26_BROWSER_SESSION ?? `stage26-${process.pid}`;
const screenshot = process.env.STAGE26_SCREENSHOT
  ?? path.join(webRoot, "test-results", "stage26-product-flow.png");
const recoveryTaskId = process.env.STAGE26_RECOVERY_TASK_ID ?? null;

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

function evaluate(expression) {
  return run(["eval", "--stdin"], { input: expression });
}

function value(expression) {
  const output = evaluate(expression);
  const line = output.split(/\r?\n/).filter(Boolean).at(-1) ?? "null";
  return JSON.parse(line);
}

async function waitFor(expression, label, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (value(expression) === true) return;
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`browser condition timed out: ${label}`);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function textContains(text) {
  return `document.body.innerText.includes(${JSON.stringify(text)})`;
}

function parseJsonOutput(output, label) {
  const start = output.indexOf("{");
  if (start < 0) throw new Error(`${label} did not return JSON: ${output}`);
  return JSON.parse(output.slice(start));
}

const started = performance.now();
let inferenceTaskId = recoveryTaskId;
let toolTaskId = null;
const routes = [];
let offlineStateVerified = false;

try {
  run(["open", `${baseUrl}/runtime${recoveryTaskId ? `?task=${encodeURIComponent(recoveryTaskId)}` : ""}`]);
  run(["wait", "--load", "networkidle"]);
  run(["console", "--clear"], { tolerate: true });
  run(["errors", "--clear"], { tolerate: true });
  await waitFor("document.body.innerText.trim().length > 500", "runtime content hydration", 20_000);
  assert(value("document.querySelectorAll('.vite-error-overlay, #webpack-dev-server-client-overlay').length") === 0, "Vite error overlay is present");
  await waitFor(textContains("Runtime live"), "runtime health");
  routes.push("/runtime");

  if (recoveryTaskId) {
    await waitFor(textContains(recoveryTaskId), "durable task after API restart");
    await waitFor(textContains("completed"), "durable terminal state after API restart");
  } else {
    run(["find", "label", "Objective", "fill", "Verify the complete local product flow with durable evidence."]);
    run(["find", "role", "button", "click", "--name", "Launch task"]);
    await waitFor("window.location.search.includes('task=')", "task URL selection");
    inferenceTaskId = value("new URLSearchParams(window.location.search).get('task')");
    assert(typeof inferenceTaskId === "string" && inferenceTaskId.length > 10, "Task ID was not retained in the URL");
    await waitFor(textContains("completed"), "inference task completion");
    await waitFor(textContains("STUB (no LLM inference):"), "rendered inference output");

    for (const [route, expected] of [
      ["agents", "Agent state map"],
      ["scheduler", "Scheduler map"],
      ["hardware", "Hardware & performance lab"],
      ["metrics", "Hardware & performance lab"],
    ]) {
      run(["open", `${baseUrl}/${route}?task=${encodeURIComponent(inferenceTaskId)}`]);
      await waitFor(textContains(expected), `${route} visualization`);
      await waitFor(textContains(inferenceTaskId), `${route} selected task continuity`);
      routes.push(`/${route}`);
    }

    run(["open", `${baseUrl}/traces?task=${encodeURIComponent(inferenceTaskId)}`]);
    await waitFor(textContains("Trace explorer"), "trace explorer");
    await waitFor(textContains("model.invocation.started"), "model trace evidence");
    run(["find", "role", "button", "click", "--name", "Replay deterministic reducers"]);
    await waitFor(textContains("Valid"), "trace replay integrity");
    routes.push("/traces");

    run(["open", `${baseUrl}/runtime`]);
    await waitFor(textContains("Safe tool probe"), "tool probe catalog");
    await waitFor("document.querySelector('.tool-probe select') !== null", "tool catalog selection readiness");
    run(["select", ".tool-probe select", "technical-explainer"]);
    await waitFor("document.querySelector('.tool-probe input') !== null", "tool catalog readiness");
    run(["find", "label", "Project-relative text path", "fill", "PROJECT_STATE.md"]);
    run(["find", "role", "button", "click", "--name", "Run bounded tool"]);
    await waitFor(textContains("# Current Project State"), "tool result rendering");
    toolTaskId = value("document.querySelector('.tool-result code')?.textContent ?? null");
    assert(typeof toolTaskId === "string" && toolTaskId.length > 10, "Tool task ID was not rendered");

    run(["open", `${baseUrl}/traces?task=${encodeURIComponent(toolTaskId)}`]);
    await waitFor(textContains("tool.output.persisted"), "persisted tool trace");
    run(["find", "role", "button", "click", "--name", "Replay deterministic reducers"]);
    await waitFor(textContains("Side effects skipped"), "tool replay side-effect boundary");

    for (const [route, expected] of [["chaos", "Chaos Lab"], ["security", "Security"]]) {
      run(["open", `${baseUrl}/${route}`]);
      await waitFor(textContains(expected), `${route} route`);
      routes.push(`/${route}`);
    }

    run(["network", "route", "**/v1/**", "--abort"]);
    run(["open", `${baseUrl}/runtime`]);
    await waitFor(textContains("API unavailable"), "visible disconnected API state", 20_000);
    offlineStateVerified = true;
    run(["network", "unroute"]);
    run(["reload"]);
    await waitFor(textContains("Runtime live"), "visible API recovery", 20_000);
  }

  const accessibility = parseJsonOutput(run(["a11y", "--tags", "wcag2a,wcag2aa", "--json"]), "accessibility audit");
  const vitals = parseJsonOutput(run(["vitals", `${baseUrl}/runtime`, "--json"]), "browser vitals");
  run(["screenshot", "--full", screenshot]);
  const consoleOutput = run(["console"], { tolerate: true });
  const pageErrors = run(["errors"], { tolerate: true });

  const result = {
    stage: 26,
    captured_at_utc: new Date().toISOString(),
    target: baseUrl,
    session,
    inference_task_id: inferenceTaskId,
    tool_task_id: toolTaskId,
    routes_verified: [...new Set(routes)],
    offline_state_verified: offlineStateVerified,
    recovery_task_verified: recoveryTaskId !== null,
    content_characters: value("document.body.innerText.trim().length"),
    error_overlay_count: value("document.querySelectorAll('.vite-error-overlay, #webpack-dev-server-client-overlay').length"),
    accessibility_violations: accessibility.violations?.length ?? 0,
    vitals,
    console_output: consoleOutput,
    page_errors: pageErrors,
    screenshot,
    elapsed_ms: Number((performance.now() - started).toFixed(3)),
  };
  if (result.error_overlay_count !== 0 || result.accessibility_violations !== 0) {
    throw new Error(`browser acceptance criteria failed: ${JSON.stringify(result)}`);
  }
  console.log(JSON.stringify(result));
} finally {
  run(["close"], { tolerate: true });
}
