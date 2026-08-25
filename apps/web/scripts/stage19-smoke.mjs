import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE19_WEB_BASE ?? "http://127.0.0.1:4173";

async function envelope(endpoint, init) {
  const response = await fetch(`${baseUrl}${endpoint}`, init);
  const payload = await response.json();
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) {
    throw new Error(`${endpoint} failed with HTTP ${response.status}`);
  }
  return { status: response.status, data: payload.data, request_id: payload.request_id ?? null };
}

function countEvents(stream, name) {
  return [...stream.matchAll(new RegExp(`^event: ${name}$`, "gm"))].length;
}

const startedAt = new Date();
const page = await fetch(`${baseUrl}/runtime`);
if (page.status !== 200) throw new Error(`/runtime failed with HTTP ${page.status}`);

const [health, agents, scheduler, hardware, models, metrics] = await Promise.all([
  envelope("/v1/health"),
  envelope("/v1/agents"),
  envelope("/v1/scheduler"),
  envelope("/v1/hardware"),
  envelope("/v1/models"),
  envelope("/v1/metrics?window_minutes=60&task_limit=8&event_limit=24&live=true"),
]);

const created = await envelope("/v1/tasks", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    agent_id: "technical-explainer",
    objective: "Explain how Stage 19 exposes real local runtime evidence.",
    workload: "interactive",
    timeout_ms: 30_000,
  }),
});

const streamStarted = performance.now();
const streamResponse = await fetch(`${baseUrl}/v1/tasks/${encodeURIComponent(created.data.task_id)}/events?after=0`);
const stream = await streamResponse.text();
const streamElapsedMs = performance.now() - streamStarted;
const inspected = await envelope(`/v1/tasks/${encodeURIComponent(created.data.task_id)}`);

const result = {
  stage: 19,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: {
    runtime_route_http_status: page.status,
    api_proxy_verified: true,
  },
  runtime: {
    health_status: health.data.status,
    runtime_status: health.data.runtime_status,
    agent_count: agents.data.agents.length,
    scheduler_policy: scheduler.data.policy,
    available_models: models.data.models.filter((model) => model.available).length,
    hardware_profile_ms: hardware.data.profile_ms,
    metrics_collection_ms: metrics.data.collection_ms,
  },
  task: {
    task_id: created.data.task_id,
    accepted_http_status: created.status,
    final_status: inspected.data.status,
    durable_state: inspected.data.durable_state,
    real_llm_calls: inspected.data.result?.metadata?.real_llm_calls ?? null,
    inference_metrics: inspected.data.result?.inference_metrics ?? null,
  },
  stream: {
    http_status: streamResponse.status,
    lifecycle_events: countEvents(stream, "lifecycle"),
    task_events: countEvents(stream, "task"),
    end_events: countEvents(stream, "end"),
    elapsed_ms: Number(streamElapsedMs.toFixed(3)),
  },
  elapsed_ms: Date.now() - startedAt.getTime(),
};

const terminalStates = new Set(["completed", "failed", "cancelled", "timed_out"]);
if (
  health.data.status !== "ok"
  || !terminalStates.has(inspected.data.status)
  || result.stream.lifecycle_events === 0
  || result.stream.task_events !== 1
  || result.stream.end_events !== 1
) {
  throw new Error(`Stage 19 smoke criteria failed: ${JSON.stringify(result)}`);
}

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage19-runtime-command-center-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");

console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
