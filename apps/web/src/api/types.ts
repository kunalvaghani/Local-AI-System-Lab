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
  task_id: string;
  sequence: number;
  status: "queued" | "running" | "completed" | "cancelled" | "timed_out" | "failed";
  workload: Workload;
  base_priority: number;
  effective_priority: number;
  queue_position_at_submit: number;
  submitted_at_utc: string;
  started_at_utc: string | null;
  finished_at_utc: string | null;
  queue_wait_ms: number | null;
  execution_ms: number | null;
  timeout_ms: number | null;
  error_code: string | null;
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

type RecentTaskTelemetry = {
  task_id: string;
  run_id: string | null;
  agent_id: string;
  state: string | null;
  created_at_utc: string;
  updated_at_utc: string;
  duration_ms: number;
  model_id: string | null;
  output_type: string | null;
  activity: { model_calls: number; tool_calls: number; router_decisions: number; recovery_attempts: number; trace_steps: number };
  scheduler: { queue_wait_ms: number | null; execution_ms: number | null };
  inference_metrics: InferenceMetrics | null;
  route_reason: string | null;
  hardware: Record<string, unknown> | null;
  failure: Record<string, unknown> | null;
};

type MetricsData = {
  generated_at_utc: string;
  window: { started_at_utc: string; ended_at_utc: string; minutes: number };
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
  recent_tasks: RecentTaskTelemetry[];
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

type ToolArgument = {
  name: string;
  type: "string" | "integer" | "boolean";
  description: string;
  required: boolean;
  default: string | number | boolean | null;
};

type ToolSummary = {
  name: string;
  description: string;
  arguments: ToolArgument[];
  permission: {
    permissions: string[];
    read_only: boolean;
    path_restricted: boolean;
    allowed_roots: string[];
  };
  timeout_ms: number;
  authorized_agent_ids: string[];
};

type ToolCatalogData = {
  tools: ToolSummary[];
  execution: { endpoint: string; mode: string; policy: string };
};

type ExecuteToolInput = {
  agent_id: string;
  tool_name: string;
  arguments: Record<string, string | number | boolean>;
};

type ToolExecutionResult = {
  request_id: string;
  task_id: string;
  agent_id: string;
  tool_name: string;
  success: boolean;
  data: Record<string, unknown>;
  duration_ms: number;
  final_state: string | null;
  state_history: StateHistoryItem[];
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

type DeterminismClass = "deterministic" | "nondeterministic" | "side_effecting" | "observational";

type TraceRun = {
  run_id: string;
  task_id: string;
  started_at_utc: string;
  finished_at_utc: string | null;
  status: string;
  model_id: string | null;
  configuration_hash: string | null;
  final_chain_hash: string | null;
  source_run_id: string | null;
};

type TraceStep = {
  run_id: string;
  ordinal: number;
  step_id: string;
  recorded_at_utc: string;
  actor: string;
  component: string;
  event_name: string;
  determinism: DeterminismClass;
  input_hash: string;
  output_hash: string;
  semantic_hash: string;
  state_from: string | null;
  state_to: string | null;
  model_id: string | null;
  configuration_hash: string | null;
  failure: { code: string; details_omitted: boolean } | null;
  previous_hash: string;
  step_hash: string;
};

type TraceData = {
  run: TraceRun;
  steps: TraceStep[];
  payload_policy: string;
};

type ReplayOutcome = "matched" | "diverged" | "observed_only" | "skipped_side_effect" | "integrity_failed";

type ReplayStep = {
  ordinal: number;
  step_id: string;
  event_name: string;
  determinism: DeterminismClass;
  outcome: ReplayOutcome;
  reason: string;
};

type ReplayReport = {
  replay_id: string;
  source_run_id: string;
  started_at_utc: string;
  finished_at_utc: string;
  status: string;
  integrity_valid: boolean;
  reconstructed_state: string | null;
  counts: Record<ReplayOutcome, number>;
  steps: ReplayStep[];
};

type ChaosScenario = {
  scenario_id: string;
  kind: string;
  point: string;
  delay_ms: number;
  max_injections: number;
};

type ChaosCatalogData = {
  armed_by_default: boolean;
  confirmation_required: boolean;
  maximum_scenarios_per_run: number;
  max_delay_ms: number;
  isolation: string;
  scenarios: ChaosScenario[];
};

type ChaosScenarioResult = {
  scenario_id: string;
  kind: string;
  target: string;
  task_id: string | null;
  expected: { state: string | null; error_code: string | null };
  actual: { state: string | null; error_code: string | null };
  injected: boolean;
  injection_count: number;
  duration_ms: number;
  baseline_ms: number;
  added_latency_ms: number;
  recovery: { attempted: boolean; succeeded: boolean | null };
  contained: boolean;
  expected_outcome_met: boolean;
  trace_steps: number;
  details: Record<string, unknown>;
};

type ChaosReport = {
  stage: number;
  purpose: string;
  run_id: string;
  started_at_utc: string;
  finished_at_utc: string;
  duration_ms: number;
  armed: boolean;
  baselines_ms: Record<string, number>;
  summary: {
    scenarios: number;
    injections: number;
    expected_outcomes_met: number;
    expected_outcome_rate_percent: number | null;
    contained: number;
    containment_rate_percent: number | null;
    completed_without_error: number;
    task_completion_rate_percent: number | null;
    recovery_attempts: number;
    recovery_successes: number;
    recovery_success_rate_percent: number | null;
    real_llm_calls: number;
    added_latency_ms: { count: number; min: number | null; p50: number | null; p95: number | null; max: number | null; mean: number | null };
  };
  scenarios: ChaosScenarioResult[];
  observability: Record<string, unknown>;
  database_integrity: string;
};

type ChaosRunData = { isolation: string; report: ChaosReport };

type SecurityCaseCatalogItem = {
  case_id: string;
  category: string;
  expected: string;
};

type SecurityCatalogData = {
  confirmation_required: boolean;
  maximum_cases_per_run: number;
  isolation: string;
  scope: string;
  cases: SecurityCaseCatalogItem[];
};

type SecurityCaseResult = {
  case_id: string;
  category: string;
  status: "PASS" | "FAIL";
  expected: string;
  actual: string;
  duration_ms: number;
  evidence: Record<string, unknown>;
};

type SecurityReport = {
  stage: number;
  purpose: string;
  disclaimer: string;
  generated_at_utc: string;
  summary: {
    cases: number;
    passed: number;
    failed: number;
    pass_rate_percent: number | null;
    total_duration_ms: number;
    real_llm_calls: number;
    integrity_check: string;
  };
  cases: SecurityCaseResult[];
};

type SecurityResultsData = {
  result_id: string;
  report: SecurityReport;
  scope: string;
};

export type {
  AgentSummary,
  AgentsData,
  ApiEnvelope,
  ApiErrorPayload,
  ChaosCatalogData,
  ChaosReport,
  ChaosRunData,
  ChaosScenario,
  ChaosScenarioResult,
  CreateTaskInput,
  ExecuteToolInput,
  Distribution,
  DeterminismClass,
  HardwareData,
  HealthData,
  InferenceMetrics,
  LifecycleEvent,
  LifecycleEventData,
  MetricsData,
  ModelsData,
  ModelSummary,
  ReplayOutcome,
  ReplayReport,
  ReplayStep,
  RecentTaskTelemetry,
  SecurityCaseCatalogItem,
  SecurityCaseResult,
  SecurityCatalogData,
  SecurityReport,
  SecurityResultsData,
  SchedulerData,
  SchedulerRequest,
  StateHistoryItem,
  TaskRecord,
  TaskResult,
  TaskStatus,
  TraceData,
  ToolCatalogData,
  ToolExecutionResult,
  TraceRun,
  TraceStep,
  StreamEndData,
  Workload,
};
