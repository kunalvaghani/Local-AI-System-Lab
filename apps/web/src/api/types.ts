type ApiEnvelope<T> = {
  data: T;
  request_id: string;
};

type ApiErrorPayload = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

type HealthData = {
  status: "ok" | "unavailable";
  runtime_status: string;
  runtime_name: string;
  persistence: {
    configured: boolean;
    schema_version: number | null;
    integrity: string | null;
  };
};

type AgentSummary = {
  agent_id: string;
  name: string;
  objective: string;
  capabilities: string[];
  tools: Array<{
    name: string;
    description: string;
    permissions: string[];
  }>;
};

type AgentsData = {
  agents: AgentSummary[];
  prompt_policy: string;
};

type SchedulerRequest = {
  request_id: string;
  task_id?: string | null;
  status: string;
  workload: string;
  priority: number;
  queue_position?: number | null;
};

type SchedulerData = {
  policy: string;
  max_workers: number;
  queue_depth: number;
  peak_queue_depth: number;
  running: number;
  submitted: number;
  started: number;
  completed: number;
  failed: number;
  cancelled: number;
  timed_out: number;
  starvation_promotions: number;
  queue_wait_p50_ms: number | null;
  queue_wait_p95_ms: number | null;
  queue_wait_max_ms: number | null;
  execution_order: string[];
  requests: SchedulerRequest[];
};

type EvidenceConfidence = "high" | "medium" | "low" | string;

type HardwareData = {
  captured_at_utc: string;
  profile_ms: number;
  cpu: {
    model: string | null;
    physical_cores: number | null;
    logical_processors: number | null;
    source: string;
    confidence: EvidenceConfidence;
  };
  ram: {
    total_mib: number | null;
    available_mib: number | null;
    used_mib: number | null;
    source: string;
    confidence: EvidenceConfidence;
  };
  gpu: {
    name: string | null;
    total_vram_mib: number | null;
    used_vram_mib: number | null;
    free_vram_mib: number | null;
    utilization_percent: number | null;
    temperature_c: number | null;
    driver_version: string | null;
    compute_capability: string | null;
    source: string;
    confidence: EvidenceConfidence;
  } | null;
  warnings: string[];
};

type ModelSummary = {
  model_id: string;
  display_name: string;
  available: boolean;
  artifact_available: boolean;
  backend_configured: boolean;
  artifact: string;
  purpose: string;
  quantization: string;
  parameter_count_billions: number;
  latency_class: string;
  benchmark: {
    tokens_per_second: number | null;
    ttft_ms: number | null;
    measured_at_utc: string;
    source: string;
    confidence: string;
    profile_id: string;
  } | null;
};

type ModelsData = {
  models: ModelSummary[];
  notes: string[];
  compute_budgets: Record<string, {
    max_generated_tokens: number;
    max_inference_calls: number;
    max_ram_mib: number;
    max_vram_mib: number;
    total_time_ms: number;
  }>;
};

type Distribution = {
  count: number;
  min: number | null;
  p50: number | null;
  p95: number | null;
  max: number | null;
  mean: number | null;
  unit: string;
};

type MetricsData = {
  generated_at_utc: string;
  collection_ms: number;
  task_states: Record<string, number>;
  totals: {
    tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    completion_rate_percent: number | null;
    model_calls_started: number;
    model_calls_completed: number;
    tool_calls: number;
    retries: number;
    recoveries: number;
    trace_runs: number;
    trace_steps: number;
    fault_injections: number;
  };
  distributions: Record<string, Distribution>;
  recent_events: Array<{
    name: string;
    task_id: string | null;
    recorded_at_utc: string;
    attributes: Record<string, unknown>;
  }>;
  recent_tasks: Array<Record<string, unknown>>;
  warnings: string[];
  sources: Record<string, string>;
};

type TaskStatus = "accepted" | "running" | "completed" | "failed" | "cancelled" | "timed_out";
type Workload = "interactive" | "standard" | "background";

type InferenceMetrics = {
  total_ms: number | null;
  ttft_ms: number | null;
  tokens_per_second: number | null;
  peak_process_ram_mib: number | null;
  vram_delta_mib: number | null;
  generated_token_runs: number | null;
  baseline_vram_used_mib?: number | null;
  generation_ms?: number | null;
  internal_load_ms?: number | null;
  model_load_ms?: number | null;
  peak_vram_used_mib?: number | null;
  prompt_eval_ms?: number | null;
  prompt_tokens?: number | null;
  prompt_tokens_per_second?: number | null;
  startup_to_ready_ms?: number | null;
};

type StateHistoryItem = {
  sequence: number;
  from_state: string | null;
  to_state: string;
  reason: string;
  recorded_at_utc: string;
};

type TaskResult = {
  task_id: string;
  agent_id: string;
  objective: string;
  output: string | null;
  model_id: string | null;
  backend_name: string | null;
  final_state: string | null;
  inference_metrics: InferenceMetrics | null;
  state_history: StateHistoryItem[];
  metadata: Record<string, unknown>;
};

type TaskRecord = {
  task_id: string;
  agent_id: string;
  objective: string;
  input_data: Record<string, unknown>;
  status: TaskStatus;
  durable_state: string | null;
  cancellation_requested: boolean;
  accepted_at_utc: string;
  started_at_utc: string | null;
  finished_at_utc: string | null;
  result: TaskResult | null;
  error: ApiErrorPayload | null;
  links: {
    self: string;
    events: string;
    trace: string;
  };
};

type CreateTaskInput = {
  agent_id: string;
  objective: string;
  workload: Workload;
  timeout_ms: number;
};

type LifecycleEvent = {
  id: string;
  event: "lifecycle" | "task" | "end";
  data: LifecycleEventData | TaskRecord | StreamEndData;
};

type LifecycleEventData = {
  name: string;
  recorded_at_utc: string;
  agent_id: string | null;
  task_id: string | null;
  state: string | null;
  data: Record<string, unknown>;
};

type StreamEndData = {
  reason: "task_terminal" | "stream_timeout" | string;
  task_continues?: boolean;
};

export type {
  AgentSummary,
  AgentsData,
  ApiEnvelope,
  ApiErrorPayload,
  CreateTaskInput,
  Distribution,
  HardwareData,
  HealthData,
  InferenceMetrics,
  LifecycleEvent,
  LifecycleEventData,
  MetricsData,
  ModelsData,
  ModelSummary,
  SchedulerData,
  StateHistoryItem,
  TaskRecord,
  TaskResult,
  TaskStatus,
  StreamEndData,
  Workload,
};
