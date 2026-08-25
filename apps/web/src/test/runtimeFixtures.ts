import type { ReplayReport, TaskRecord, TraceData } from "../api/types";

const taskFixture: TaskRecord = {
  task_id: "task-stage20-test",
  agent_id: "technical-explainer",
  objective: "Explain the bounded local runtime.",
  input_data: { workload: "standard" },
  status: "running",
  durable_state: "executing",
  cancellation_requested: false,
  accepted_at_utc: "2026-08-25T12:00:00+00:00",
  started_at_utc: "2026-08-25T12:00:00.010000+00:00",
  finished_at_utc: null,
  result: null,
  error: null,
  links: {
    self: "/v1/tasks/task-stage20-test",
    events: "/v1/tasks/task-stage20-test/events",
    trace: "/v1/tasks/task-stage20-test/trace",
  },
};

const traceFixture: TraceData = {
  run: {
    run_id: "run-stage21-test",
    task_id: taskFixture.task_id,
    started_at_utc: "2026-08-25T12:00:00.000000+00:00",
    finished_at_utc: "2026-08-25T12:00:00.125000+00:00",
    status: "completed",
    model_id: "qwen-test",
    configuration_hash: "config-hash-stage21",
    final_chain_hash: "chain-final-stage21",
    source_run_id: null,
  },
  steps: [
    { run_id: "run-stage21-test", ordinal: 0, step_id: "step-created", recorded_at_utc: "2026-08-25T12:00:00.000000+00:00", actor: "agent-runtime", component: "state-machine", event_name: "task.created", determinism: "deterministic", input_hash: "input-0", output_hash: "output-0", semantic_hash: "semantic-0", state_from: null, state_to: null, model_id: null, configuration_hash: null, failure: null, previous_hash: "genesis", step_hash: "step-hash-0" },
    { run_id: "run-stage21-test", ordinal: 1, step_id: "step-state", recorded_at_utc: "2026-08-25T12:00:00.010000+00:00", actor: "agent-runtime", component: "state-machine", event_name: "task.state.changed", determinism: "deterministic", input_hash: "input-1", output_hash: "output-1", semantic_hash: "semantic-1", state_from: "planning", state_to: "executing", model_id: null, configuration_hash: null, failure: null, previous_hash: "step-hash-0", step_hash: "step-hash-1" },
    { run_id: "run-stage21-test", ordinal: 2, step_id: "step-model-started", recorded_at_utc: "2026-08-25T12:00:00.025000+00:00", actor: "inference-backend", component: "model-inference", event_name: "model.invocation.started", determinism: "nondeterministic", input_hash: "input-2", output_hash: "output-2", semantic_hash: "semantic-2", state_from: null, state_to: null, model_id: "qwen-test", configuration_hash: "config-hash-stage21", failure: null, previous_hash: "step-hash-1", step_hash: "step-hash-2" },
    { run_id: "run-stage21-test", ordinal: 3, step_id: "step-tool", recorded_at_utc: "2026-08-25T12:00:00.090000+00:00", actor: "tool-executor", component: "tool-runtime", event_name: "tool.execution.completed", determinism: "side_effecting", input_hash: "input-3", output_hash: "output-3", semantic_hash: "semantic-3", state_from: null, state_to: null, model_id: null, configuration_hash: null, failure: null, previous_hash: "step-hash-2", step_hash: "step-hash-3" },
    { run_id: "run-stage21-test", ordinal: 4, step_id: "step-complete", recorded_at_utc: "2026-08-25T12:00:00.125000+00:00", actor: "agent-runtime", component: "state-machine", event_name: "task.completed", determinism: "deterministic", input_hash: "input-4", output_hash: "output-4", semantic_hash: "semantic-4", state_from: null, state_to: null, model_id: null, configuration_hash: null, failure: null, previous_hash: "step-hash-3", step_hash: "chain-final-stage21" },
  ],
  payload_policy: "input/output payloads and failure details are omitted; integrity hashes are exposed",
};

const replayFixture: ReplayReport = {
  replay_id: "replay-stage21-test",
  source_run_id: traceFixture.run.run_id,
  started_at_utc: "2026-08-25T12:01:00+00:00",
  finished_at_utc: "2026-08-25T12:01:00.005000+00:00",
  status: "matched",
  integrity_valid: true,
  reconstructed_state: "executing",
  counts: { matched: 3, diverged: 0, observed_only: 1, skipped_side_effect: 1, integrity_failed: 0 },
  steps: traceFixture.steps.map((step) => ({ ordinal: step.ordinal, step_id: step.step_id, event_name: step.event_name, determinism: step.determinism, outcome: step.determinism === "deterministic" ? "matched" : step.determinism === "side_effecting" ? "skipped_side_effect" : "observed_only", reason: step.determinism === "deterministic" ? "canonical hashes and deterministic reducer matched" : step.determinism === "side_effecting" ? "side-effecting operation was not re-executed" : "nondeterministic or environmental evidence was integrity-checked only" })),
};

const fixtures: Record<string, unknown> = {
  "/v1/health": {
    status: "ok",
    runtime_status: "running",
    runtime_name: "stage15-stub-runtime",
    persistence: { configured: true, schema_version: 2, integrity: "ok" },
  },
  "/v1/agents": {
    agents: [{
      agent_id: "technical-explainer",
      name: "Technical Explainer",
      objective: "Explain local runtime evidence.",
      capabilities: ["explanation", "local-inference"],
      tools: [{ name: "local-docs", description: "Read bounded local documentation.", permissions: ["read"] }],
    }],
    prompt_policy: "bounded",
  },
  "/v1/scheduler": {
    policy: "priority",
    max_workers: 1,
    queue_depth: 2,
    peak_queue_depth: 2,
    running: 1,
    submitted: 3,
    started: 1,
    completed: 0,
    failed: 0,
    cancelled: 0,
    timed_out: 0,
    starvation_promotions: 0,
    queue_wait_p50_ms: 0.2,
    queue_wait_p95_ms: 0.2,
    queue_wait_max_ms: 0.2,
    execution_order: ["task-stage20-test"],
    requests: [
      { request_id: "scheduler-running", task_id: "task-stage20-test", sequence: 1, status: "running", workload: "standard", base_priority: 5, effective_priority: 5, queue_position_at_submit: 0, submitted_at_utc: "2026-08-25T12:00:00+00:00", started_at_utc: "2026-08-25T12:00:00.010000+00:00", finished_at_utc: null, queue_wait_ms: 0.2, execution_ms: null, timeout_ms: 30000, error_code: null },
      { request_id: "scheduler-background", task_id: "task-background", sequence: 2, status: "queued", workload: "background", base_priority: 2, effective_priority: 2, queue_position_at_submit: 1, submitted_at_utc: "2026-08-25T12:00:00.020000+00:00", started_at_utc: null, finished_at_utc: null, queue_wait_ms: null, execution_ms: null, timeout_ms: 30000, error_code: null },
      { request_id: "scheduler-interactive", task_id: "task-interactive", sequence: 3, status: "queued", workload: "interactive", base_priority: 8, effective_priority: 8, queue_position_at_submit: 2, submitted_at_utc: "2026-08-25T12:00:00.030000+00:00", started_at_utc: null, finished_at_utc: null, queue_wait_ms: null, execution_ms: null, timeout_ms: 30000, error_code: null },
    ],
  },
  "/v1/hardware": {
    captured_at_utc: "2026-08-25T12:00:00+00:00",
    profile_ms: 14.2,
    cpu: { model: "Test CPU", physical_cores: null, logical_processors: 16, source: "test", confidence: "high" },
    ram: { total_mib: 32768, available_mib: 20480, used_mib: 12288, source: "test", confidence: "high" },
    gpu: { name: "Test GPU", total_vram_mib: 4096, used_vram_mib: 1024, free_vram_mib: 3072, utilization_percent: 12, temperature_c: 49, driver_version: "test", compute_capability: null, source: "test", confidence: "high" },
    warnings: ["Physical core count unavailable"],
  },
  "/v1/models": {
    models: [{
      model_id: "qwen-test",
      display_name: "Qwen 2.5 1.5B",
      available: true,
      artifact_available: true,
      backend_configured: true,
      artifact: "registry entry",
      purpose: "local explanation",
      quantization: "Q4_K_M",
      parameter_count_billions: 1.5,
      latency_class: "interactive",
      benchmark: { tokens_per_second: 100.9, ttft_ms: 1655.2, measured_at_utc: "2026-08-25T12:00:00+00:00", source: "retained benchmark", confidence: "high", profile_id: "test" },
    }, {
      model_id: "qwen-compact-test",
      display_name: "Qwen 2.5 0.5B",
      available: false,
      artifact_available: false,
      backend_configured: false,
      artifact: "registry entry",
      purpose: "uninstalled compact candidate",
      quantization: "Q4_K_M",
      parameter_count_billions: 0.5,
      latency_class: "fast",
      benchmark: null,
    }],
    notes: ["Compact candidate is unavailable and not benchmarked."],
    compute_budgets: { standard: { max_generated_tokens: 64, max_inference_calls: 1, max_ram_mib: 2200, max_vram_mib: 1536, total_time_ms: 30000 } },
  },
  "/v1/metrics": {
    generated_at_utc: "2026-08-25T12:00:00+00:00",
    window: { started_at_utc: "2026-08-25T11:00:00+00:00", ended_at_utc: "2026-08-25T12:00:00+00:00", minutes: 60 },
    collection_ms: 8.4,
    task_states: { completed: 2 },
    totals: { tasks: 2, completed_tasks: 2, failed_tasks: 0, completion_rate_percent: 100, model_calls_started: 2, model_calls_completed: 2, tool_calls: 0, retries: 0, recoveries: 0, trace_runs: 2, trace_steps: 32, fault_injections: 0 },
    distributions: {
      ttft_ms: { count: 2, min: 1450, p50: 1600, p95: 1735, max: 1750, mean: 1600, unit: "ms" },
      generation_tokens_per_second: { count: 2, min: 96.2, p50: 99.8, p95: 103.04, max: 103.4, mean: 99.8, unit: "tokens/s" },
      queue_wait_ms: { count: 2, min: 0.1, p50: 0.2, p95: 0.29, max: 0.3, mean: 0.2, unit: "ms" },
      scheduler_execution_ms: { count: 2, min: 1800, p50: 1900, p95: 1990, max: 2000, mean: 1900, unit: "ms" },
      inference_total_ms: { count: 2, min: 2300, p50: 2450, p95: 2585, max: 2600, mean: 2450, unit: "ms" },
      task_duration_ms: { count: 2, min: 2800, p50: 3000, p95: 3180, max: 3200, mean: 3000, unit: "ms" },
      peak_process_ram_mib: { count: 2, min: 1320, p50: 1332, p95: 1342.8, max: 1344, mean: 1332, unit: "MiB" },
      vram_delta_mib: { count: 0, min: null, p50: null, p95: null, max: null, mean: null, unit: "MiB" },
    },
    recent_events: [],
    recent_tasks: [
      { task_id: "task-history-new", run_id: "run-history-new", agent_id: "technical-explainer", state: "completed", created_at_utc: "2026-08-25T11:58:00+00:00", updated_at_utc: "2026-08-25T11:58:03.200000+00:00", duration_ms: 3200, model_id: "qwen-test", output_type: "inference", activity: { model_calls: 1, tool_calls: 0, router_decisions: 1, recovery_attempts: 0, trace_steps: 16 }, scheduler: { queue_wait_ms: 0.3, execution_ms: 2000 }, inference_metrics: { total_ms: 2600, ttft_ms: 1750, tokens_per_second: 96.2, peak_process_ram_mib: 1344, vram_delta_mib: null, generated_token_runs: 1 }, route_reason: "available local baseline", hardware: null, failure: null },
      { task_id: "task-history-old", run_id: "run-history-old", agent_id: "technical-explainer", state: "completed", created_at_utc: "2026-08-25T11:30:00+00:00", updated_at_utc: "2026-08-25T11:30:02.800000+00:00", duration_ms: 2800, model_id: "qwen-test", output_type: "inference", activity: { model_calls: 1, tool_calls: 0, router_decisions: 1, recovery_attempts: 0, trace_steps: 16 }, scheduler: { queue_wait_ms: 0.1, execution_ms: 1800 }, inference_metrics: { total_ms: 2300, ttft_ms: 1450, tokens_per_second: 103.4, peak_process_ram_mib: 1320, vram_delta_mib: null, generated_token_runs: 1 }, route_reason: "available local baseline", hardware: null, failure: null },
    ],
    warnings: [],
    sources: { latency_and_inference: "SQLite outputs plus scheduler timestamps", live_hardware: "hardware_profiler.snapshot()" },
  },
};

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify({ data, request_id: "request-stage20-test" }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function runtimeFetch(input: RequestInfo | URL, init?: RequestInit) {
  const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url, window.location.origin);
  if (url.pathname === "/v1/tasks" && init?.method === "POST") return Promise.resolve(jsonResponse(taskFixture, 202));
  if (url.pathname === taskFixture.links.trace) return Promise.resolve(jsonResponse(traceFixture));
  if (url.pathname === `/v1/traces/${traceFixture.run.run_id}/replay` && init?.method === "POST") return Promise.resolve(jsonResponse(replayFixture));
  if (url.pathname === `/v1/tasks/${taskFixture.task_id}` && init?.method === "DELETE") return Promise.resolve(jsonResponse({ ...taskFixture, cancellation_requested: true }, 202));
  if (url.pathname === `/v1/tasks/${taskFixture.task_id}`) return Promise.resolve(jsonResponse(taskFixture));
  return Promise.resolve(jsonResponse(fixtures[url.pathname]));
}

class EventSourceFixture {
  static instances: EventSourceFixture[] = [];
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;
  readonly CONNECTING = 0;
  readonly OPEN = 1;
  readonly CLOSED = 2;
  readonly url: string;
  readonly withCredentials = false;
  readyState = 0;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  private listeners = new Map<string, EventListenerOrEventListenerObject[]>();

  constructor(url: string | URL) {
    this.url = String(url);
    EventSourceFixture.instances.push(this);
  }

  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }
  removeEventListener() {}
  dispatchEvent() { return true; }
  close() { this.readyState = EventSourceFixture.CLOSED; }
  open() {
    this.readyState = EventSourceFixture.OPEN;
    this.onopen?.(new Event("open"));
  }
  emit(type: string, id: string, data: Record<string, unknown>) {
    const event = new MessageEvent(type, { data: JSON.stringify(data), lastEventId: id });
    for (const listener of this.listeners.get(type) ?? []) {
      if (typeof listener === "function") listener(event);
      else listener.handleEvent(event);
    }
  }
}

export { EventSourceFixture, replayFixture, runtimeFetch, taskFixture, traceFixture };
