import type { TaskRecord } from "../api/types";

const taskFixture: TaskRecord = {
  task_id: "task-stage20-test",
  agent_id: "technical-explainer",
  objective: "Explain the bounded local runtime.",
  input_data: {},
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
    gpu: { name: "Test GPU", total_vram_mib: 4096, used_vram_mib: null, free_vram_mib: null, utilization_percent: 12, temperature_c: 49, driver_version: "test", compute_capability: null, source: "test", confidence: "high" },
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
    }],
    notes: [],
    compute_budgets: {},
  },
  "/v1/metrics": {
    generated_at_utc: "2026-08-25T12:00:00+00:00",
    collection_ms: 8.4,
    task_states: { completed: 1 },
    totals: { tasks: 1, completed_tasks: 1, failed_tasks: 0, completion_rate_percent: 100, model_calls_started: 0, model_calls_completed: 0, tool_calls: 0, retries: 0, recoveries: 0, trace_runs: 1, trace_steps: 5, fault_injections: 0 },
    distributions: {},
    recent_events: [],
    recent_tasks: [],
    warnings: [],
    sources: {},
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

export { EventSourceFixture, runtimeFetch, taskFixture };
