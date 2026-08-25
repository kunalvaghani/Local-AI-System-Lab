import type {
  AgentsData,
  ApiEnvelope,
  ApiErrorPayload,
  ChaosCatalogData,
  ChaosRunData,
  CreateTaskInput,
  HardwareData,
  HealthData,
  MetricsData,
  ModelsData,
  ReplayReport,
  SchedulerData,
  SecurityCatalogData,
  SecurityResultsData,
  TaskRecord,
  TraceData,
} from "./types";

class RuntimeApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly details: Record<string, unknown>;

  constructor(status: number, payload: ApiErrorPayload, requestId: string | null) {
    super(payload.message);
    this.name = "RuntimeApiError";
    this.status = status;
    this.code = payload.code;
    this.requestId = requestId;
    this.details = payload.details ?? {};
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function requestData<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "same-origin",
  });
  const payload: unknown = await response.json();

  if (!isObject(payload)) {
    throw new RuntimeApiError(response.status, {
      code: "api_response_invalid",
      message: "The runtime returned a non-object response.",
    }, null);
  }

  const requestId = typeof payload.request_id === "string" ? payload.request_id : null;
  if (!response.ok) {
    const error = isObject(payload.error) ? payload.error : {};
    throw new RuntimeApiError(response.status, {
      code: typeof error.code === "string" ? error.code : "api_request_failed",
      message: typeof error.message === "string" ? error.message : `Runtime request failed (${response.status}).`,
      details: isObject(error.details) ? error.details : {},
    }, requestId);
  }

  if (!("data" in payload)) {
    throw new RuntimeApiError(response.status, {
      code: "api_response_invalid",
      message: "The runtime response omitted its data envelope.",
    }, requestId);
  }

  return (payload as ApiEnvelope<T>).data;
}

const runtimeApi = {
  health: (signal?: AbortSignal) => requestData<HealthData>("/v1/health", { signal }),
  agents: (signal?: AbortSignal) => requestData<AgentsData>("/v1/agents", { signal }),
  scheduler: (signal?: AbortSignal) => requestData<SchedulerData>("/v1/scheduler", { signal }),
  hardware: (signal?: AbortSignal) => requestData<HardwareData>("/v1/hardware", { signal }),
  models: (signal?: AbortSignal) => requestData<ModelsData>("/v1/models", { signal }),
  metrics: (signal?: AbortSignal) => requestData<MetricsData>(
    "/v1/metrics?window_minutes=60&task_limit=8&event_limit=24&live=false",
    { signal },
  ),
  chaosCatalog: (signal?: AbortSignal) => requestData<ChaosCatalogData>("/v1/chaos", { signal }),
  runChaos: (scenarios: string[]) => requestData<ChaosRunData>("/v1/chaos", {
    method: "POST",
    body: JSON.stringify({ confirm: true, scenarios }),
  }),
  securityCatalog: (signal?: AbortSignal) => requestData<SecurityCatalogData>("/v1/security", { signal }),
  securityResults: (signal?: AbortSignal) => requestData<SecurityResultsData>("/v1/security/results", { signal }),
  runSecurity: (cases: string[]) => requestData<SecurityResultsData>("/v1/security", {
    method: "POST",
    body: JSON.stringify({ confirm: true, cases }),
  }),
  createTask: (input: CreateTaskInput) => requestData<TaskRecord>("/v1/tasks", {
    method: "POST",
    body: JSON.stringify(input),
  }),
  task: (taskId: string, signal?: AbortSignal) => requestData<TaskRecord>(
    `/v1/tasks/${encodeURIComponent(taskId)}`,
    { signal },
  ),
  cancelTask: (taskId: string) => requestData<TaskRecord>(
    `/v1/tasks/${encodeURIComponent(taskId)}`,
    { method: "DELETE" },
  ),
  taskTrace: (taskId: string, signal?: AbortSignal) => requestData<TraceData>(
    `/v1/tasks/${encodeURIComponent(taskId)}/trace`,
    { signal },
  ),
  replayTrace: (runId: string) => requestData<ReplayReport>(
    `/v1/traces/${encodeURIComponent(runId)}/replay`,
    { method: "POST", body: JSON.stringify({}) },
  ),
};

export { RuntimeApiError, runtimeApi };
