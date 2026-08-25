import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE22_WEB_BASE ?? "http://127.0.0.1:4173";

async function envelope(endpoint, init) {
  const response = await fetch(`${baseUrl}${endpoint}`, init);
  const payload = await response.json();
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) throw new Error(`${endpoint} failed with HTTP ${response.status}`);
  return { status: response.status, data: payload.data };
}

const startedAt = performance.now();
const [hardwareRoute, metricsRoute] = await Promise.all([fetch(`${baseUrl}/hardware`), fetch(`${baseUrl}/metrics`)]);
const evidenceStarted = performance.now();
const [hardware, models, scheduler] = await Promise.all([envelope("/v1/hardware"), envelope("/v1/models"), envelope("/v1/scheduler")]);
const initialMetrics = await envelope("/v1/metrics?window_minutes=60&task_limit=8&event_limit=24&live=false");
const evidenceRetrievalMs = performance.now() - evidenceStarted;

const created = await envelope("/v1/tasks", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ agent_id: "technical-explainer", objective: "Explain how Stage 22 investigates measured local inference and resource behavior.", workload: "standard", timeout_ms: 30_000 }),
});
const streamResponse = await fetch(`${baseUrl}/v1/tasks/${encodeURIComponent(created.data.task_id)}/events?after=0`);
await streamResponse.text();
const [task, finalMetrics] = await Promise.all([
  envelope(`/v1/tasks/${encodeURIComponent(created.data.task_id)}`),
  envelope("/v1/metrics?window_minutes=60&task_limit=8&event_limit=24&live=false"),
]);
const recentTask = finalMetrics.data.recent_tasks.find((item) => item.task_id === created.data.task_id);
const availableModel = models.data.models.find((model) => model.available);
const distributions = finalMetrics.data.distributions;

const result = {
  stage: 22,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: { hardware_route_http_status: hardwareRoute.status, metrics_route_http_status: metricsRoute.status, api_proxy_verified: true },
  hardware: {
    captured_at_utc: hardware.data.captured_at_utc,
    profile_ms: hardware.data.profile_ms,
    cpu_model: hardware.data.cpu.model,
    logical_processors: hardware.data.cpu.logical_processors,
    physical_cores: hardware.data.cpu.physical_cores,
    cpu_source: hardware.data.cpu.source,
    ram_total_mib: hardware.data.ram.total_mib,
    ram_used_mib: hardware.data.ram.used_mib,
    ram_source: hardware.data.ram.source,
    gpu_name: hardware.data.gpu?.name ?? null,
    gpu_utilization_percent: hardware.data.gpu?.utilization_percent ?? null,
    vram_total_mib: hardware.data.gpu?.total_vram_mib ?? null,
    vram_used_mib: hardware.data.gpu?.used_vram_mib ?? null,
    gpu_source: hardware.data.gpu?.source ?? null,
    warnings: hardware.data.warnings,
  },
  model: {
    selected_task_model_id: task.data.result?.model_id ?? null,
    available_registry_model_id: availableModel?.model_id ?? null,
    retained_ttft_ms: availableModel?.benchmark?.ttft_ms ?? null,
    retained_tokens_per_second: availableModel?.benchmark?.tokens_per_second ?? null,
    retained_profile_id: availableModel?.benchmark?.profile_id ?? null,
  },
  workload: {
    task_id: task.data.task_id,
    status: task.data.status,
    durable_state: task.data.durable_state,
    inference_total_ms: task.data.result?.inference_metrics?.total_ms ?? null,
    ttft_ms: task.data.result?.inference_metrics?.ttft_ms ?? null,
    tokens_per_second: task.data.result?.inference_metrics?.tokens_per_second ?? null,
    queue_wait_ms: recentTask?.scheduler?.queue_wait_ms ?? null,
    scheduler_execution_ms: recentTask?.scheduler?.execution_ms ?? null,
  },
  history: {
    initial_tasks: initialMetrics.data.totals.tasks,
    final_tasks: finalMetrics.data.totals.tasks,
    recent_tasks: finalMetrics.data.recent_tasks.length,
    selected_task_present: Boolean(recentTask),
    ttft_samples: distributions.ttft_ms.count,
    throughput_samples: distributions.generation_tokens_per_second.count,
    queue_wait_samples: distributions.queue_wait_ms.count,
    task_duration_samples: distributions.task_duration_ms.count,
    window_minutes: finalMetrics.data.window.minutes,
    collection_ms: finalMetrics.data.collection_ms,
  },
  scheduler: { policy: scheduler.data.policy, max_workers: scheduler.data.max_workers },
  evidence_retrieval_ms: Number(evidenceRetrievalMs.toFixed(3)),
  elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
};

if (hardwareRoute.status !== 200 || metricsRoute.status !== 200 || !hardware.data.cpu.source || hardware.data.ram.total_mib == null || !availableModel?.benchmark || task.data.status !== "completed" || !recentTask || finalMetrics.data.totals.tasks <= initialMetrics.data.totals.tasks) throw new Error(`Stage 22 smoke criteria failed: ${JSON.stringify(result)}`);

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage22-hardware-performance-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
