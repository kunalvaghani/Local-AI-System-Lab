import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE21_WEB_BASE ?? "http://127.0.0.1:4173";

async function envelope(endpoint, init) {
  const response = await fetch(`${baseUrl}${endpoint}`, init);
  const payload = await response.json();
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) throw new Error(`${endpoint} failed with HTTP ${response.status}`);
  return { status: response.status, data: payload.data };
}

const startedAt = performance.now();
const route = await fetch(`${baseUrl}/traces`);
const created = await envelope("/v1/tasks", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ agent_id: "technical-explainer", objective: "Explain how Stage 21 visually debugs a redacted deterministic trace.", workload: "interactive", timeout_ms: 30_000 }),
});
const streamResponse = await fetch(`${baseUrl}/v1/tasks/${encodeURIComponent(created.data.task_id)}/events?after=0`);
await streamResponse.text();

const traceStarted = performance.now();
const trace = await envelope(`/v1/tasks/${encodeURIComponent(created.data.task_id)}/trace`);
const traceRetrievalMs = performance.now() - traceStarted;
const replayStarted = performance.now();
const replay = await envelope(`/v1/traces/${encodeURIComponent(trace.data.run.run_id)}/replay`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
const replayMs = performance.now() - replayStarted;
const determinism = trace.data.steps.reduce((counts, step) => {
  counts[step.determinism] = (counts[step.determinism] ?? 0) + 1;
  return counts;
}, {});
const payloadRedacted = trace.data.steps.every((step) => !("input" in step) && !("output" in step));
const recordedDurationMs = new Date(trace.data.run.finished_at_utc).getTime() - new Date(trace.data.run.started_at_utc).getTime();

const result = {
  stage: 21,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: { trace_route_http_status: route.status, api_proxy_verified: true },
  trace: {
    task_id: created.data.task_id,
    run_id: trace.data.run.run_id,
    status: trace.data.run.status,
    steps: trace.data.steps.length,
    deterministic_steps: determinism.deterministic ?? 0,
    nondeterministic_steps: determinism.nondeterministic ?? 0,
    observational_steps: determinism.observational ?? 0,
    side_effecting_steps: determinism.side_effecting ?? 0,
    state_transitions: trace.data.steps.filter((step) => step.event_name === "task.state.changed").length,
    model_steps: trace.data.steps.filter((step) => step.event_name.startsWith("model.")).length,
    tool_steps: trace.data.steps.filter((step) => step.event_name.startsWith("tool.")).length,
    payload_redacted: payloadRedacted,
    recorded_duration_ms: recordedDurationMs,
    retrieval_ms: Number(traceRetrievalMs.toFixed(3)),
  },
  replay: {
    status: replay.data.status,
    integrity_valid: replay.data.integrity_valid,
    reconstructed_state: replay.data.reconstructed_state,
    counts: replay.data.counts,
    duration_ms: Number(replayMs.toFixed(3)),
  },
  elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
};

if (route.status !== 200 || trace.data.steps.length === 0 || !payloadRedacted || !replay.data.integrity_valid || replay.data.steps.length !== trace.data.steps.length) throw new Error(`Stage 21 smoke criteria failed: ${JSON.stringify(result)}`);

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage21-trace-replay-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
