import type { LifecycleEvent, LifecycleEventData, SchedulerRequest, TaskRecord } from "../../api/types";

type AdmissionEvidence = {
  action: string;
  permitted: boolean;
  reason: string;
  confidence: string;
  recommended_context_tokens: number | null;
  recommended_gpu_layers: number | null;
  fallback_model_id: string | null;
  constraints: string[];
  estimate: {
    model_id: string;
    context_tokens: number;
    gpu_layers: number;
    predicted_host_ram_mib: number;
    predicted_vram_mib: number;
  } | null;
};

function objectValue(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

function admissionValue(value: unknown): AdmissionEvidence | null {
  const record = objectValue(value);
  if (!record || typeof record.action !== "string" || typeof record.permitted !== "boolean" || typeof record.reason !== "string") return null;
  const estimate = objectValue(record.estimate);
  const parsedEstimate = estimate
    && typeof estimate.model_id === "string"
    && typeof estimate.context_tokens === "number"
    && typeof estimate.gpu_layers === "number"
    && typeof estimate.predicted_host_ram_mib === "number"
    && typeof estimate.predicted_vram_mib === "number"
    ? {
      model_id: estimate.model_id,
      context_tokens: estimate.context_tokens,
      gpu_layers: estimate.gpu_layers,
      predicted_host_ram_mib: estimate.predicted_host_ram_mib,
      predicted_vram_mib: estimate.predicted_vram_mib,
    }
    : null;

  return {
    action: record.action,
    permitted: record.permitted,
    reason: record.reason,
    confidence: typeof record.confidence === "string" ? record.confidence : "unreported",
    recommended_context_tokens: typeof record.recommended_context_tokens === "number" ? record.recommended_context_tokens : null,
    recommended_gpu_layers: typeof record.recommended_gpu_layers === "number" ? record.recommended_gpu_layers : null,
    fallback_model_id: typeof record.fallback_model_id === "string" ? record.fallback_model_id : null,
    constraints: Array.isArray(record.constraints) ? record.constraints.filter((item): item is string => typeof item === "string") : [],
    estimate: parsedEstimate,
  };
}

function admissionFor(task: TaskRecord | undefined, events: LifecycleEvent[]) {
  const metadata = objectValue(task?.result?.metadata);
  const durable = admissionValue(metadata?.admission);
  if (durable) return durable;
  for (const event of [...events].reverse()) {
    if (event.event !== "lifecycle") continue;
    const lifecycle = event.data as LifecycleEventData;
    if (lifecycle.name !== "admission.evaluated") continue;
    const direct = admissionValue(lifecycle.data);
    if (direct) return direct;
    const nested = admissionValue(objectValue(lifecycle.data)?.admission);
    if (nested) return nested;
  }
  return null;
}

function schedulerRequestFor(task: TaskRecord | undefined): SchedulerRequest | null {
  const metadata = objectValue(task?.result?.metadata);
  const record = objectValue(metadata?.scheduler);
  if (!record
    || typeof record.request_id !== "string"
    || typeof record.task_id !== "string"
    || typeof record.sequence !== "number"
    || typeof record.status !== "string"
    || typeof record.workload !== "string"
    || typeof record.base_priority !== "number"
    || typeof record.effective_priority !== "number"
    || typeof record.queue_position_at_submit !== "number"
    || typeof record.submitted_at_utc !== "string") return null;
  if (!["queued", "running", "completed", "cancelled", "timed_out", "failed"].includes(record.status)) return null;
  if (!["interactive", "standard", "background"].includes(record.workload)) return null;

  return {
    request_id: record.request_id,
    task_id: record.task_id,
    sequence: record.sequence,
    status: record.status as SchedulerRequest["status"],
    workload: record.workload as SchedulerRequest["workload"],
    base_priority: record.base_priority,
    effective_priority: record.effective_priority,
    queue_position_at_submit: record.queue_position_at_submit,
    submitted_at_utc: record.submitted_at_utc,
    started_at_utc: typeof record.started_at_utc === "string" ? record.started_at_utc : null,
    finished_at_utc: typeof record.finished_at_utc === "string" ? record.finished_at_utc : null,
    queue_wait_ms: typeof record.queue_wait_ms === "number" ? record.queue_wait_ms : null,
    execution_ms: typeof record.execution_ms === "number" ? record.execution_ms : null,
    timeout_ms: typeof record.timeout_ms === "number" ? record.timeout_ms : null,
    error_code: typeof record.error_code === "string" ? record.error_code : null,
  };
}

export { admissionFor, schedulerRequestFor };
export type { AdmissionEvidence };
