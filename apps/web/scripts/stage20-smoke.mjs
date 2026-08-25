import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE20_WEB_BASE ?? "http://127.0.0.1:4173";

async function envelope(endpoint, init) {
  const response = await fetch(`${baseUrl}${endpoint}`, init);
  const payload = await response.json();
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) throw new Error(`${endpoint} failed with HTTP ${response.status}`);
  return { status: response.status, data: payload.data };
}

function countEvents(stream, name) {
  return [...stream.matchAll(new RegExp(`^event: ${name}$`, "gm"))].length;
}

const startedAt = performance.now();
const [agentsPage, schedulerPage, agents] = await Promise.all([
  fetch(`${baseUrl}/agents`),
  fetch(`${baseUrl}/scheduler`),
  envelope("/v1/agents"),
]);

const created = await envelope("/v1/tasks", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    agent_id: "technical-explainer",
    objective: "Explain how Stage 20 visualizes agent and scheduler evidence.",
    workload: "interactive",
    timeout_ms: 30_000,
  }),
});

const streamResponse = await fetch(`${baseUrl}/v1/tasks/${encodeURIComponent(created.data.task_id)}/events?after=0`);
const stream = await streamResponse.text();
const [task, scheduler] = await Promise.all([
  envelope(`/v1/tasks/${encodeURIComponent(created.data.task_id)}`),
  envelope("/v1/scheduler"),
]);
const request = scheduler.data.requests.find((item) => item.task_id === created.data.task_id) ?? task.data.result?.metadata?.scheduler ?? null;
const admission = task.data.result?.metadata?.admission ?? null;

const result = {
  stage: 20,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: { agents_route_http_status: agentsPage.status, scheduler_route_http_status: schedulerPage.status, api_proxy_verified: true },
  agents: { count: agents.data.agents.length, selected_agent_id: task.data.agent_id, prompt_policy: agents.data.prompt_policy },
  task: { task_id: task.data.task_id, final_status: task.data.status, durable_state: task.data.durable_state, state_transitions: task.data.result?.state_history?.length ?? 0 },
  admission: admission ? { action: admission.action, permitted: admission.permitted, confidence: admission.confidence, predicted_host_ram_mib: admission.estimate?.predicted_host_ram_mib ?? null, predicted_vram_mib: admission.estimate?.predicted_vram_mib ?? null } : null,
  scheduler: request ? { policy: scheduler.data.policy, request_status: request.status, workload: request.workload, base_priority: request.base_priority, effective_priority: request.effective_priority, queue_wait_ms: request.queue_wait_ms, execution_ms: request.execution_ms } : null,
  stream: { http_status: streamResponse.status, lifecycle_events: countEvents(stream, "lifecycle"), task_events: countEvents(stream, "task"), end_events: countEvents(stream, "end") },
  elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
};

if (agentsPage.status !== 200 || schedulerPage.status !== 200 || !request || task.data.result?.state_history?.length === 0 || result.stream.lifecycle_events === 0 || result.stream.task_events !== 1 || result.stream.end_events !== 1) {
  throw new Error(`Stage 20 smoke criteria failed: ${JSON.stringify(result)}`);
}

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage20-agent-scheduler-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
