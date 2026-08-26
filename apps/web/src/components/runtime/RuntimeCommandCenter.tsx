import type { RuntimeApiError } from "../../api/client";
import { useSelectedTaskId } from "../../hooks/useSelectedTaskId";
import { useTaskEvents } from "../../hooks/useTaskEvents";
import {
  useAgentsQuery,
  useCancelTaskMutation,
  useCreateTaskMutation,
  useHardwareQuery,
  useHealthQuery,
  useMetricsQuery,
  useModelsQuery,
  useSchedulerQuery,
  useTaskQuery,
} from "../../query/runtimeQueries";
import { StatusToken } from "../StatusToken";
import { EvidenceValue } from "./EvidenceValue";
import { ExecutionRail } from "./ExecutionRail";
import { TaskComposer } from "./TaskComposer";
import { TaskInspector } from "./TaskInspector";

function percent(used: number | null | undefined, total: number | null | undefined) {
  return used == null || total == null || total <= 0 ? null : (used / total) * 100;
}

function formatNumber(value: number | null | undefined, maximumFractionDigits = 1) {
  return value == null
    ? "Unavailable"
    : new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(value);
}

function formatMemory(value: number | null | undefined) {
  if (value == null) {
    return "Unavailable";
  }
  return value >= 1024 ? `${formatNumber(value / 1024)} GiB` : `${formatNumber(value, 0)} MiB`;
}

function queryError(error: Error | null) {
  if (!error) {
    return null;
  }
  const runtimeError = error as RuntimeApiError;
  return `${runtimeError.message}${runtimeError.requestId ? ` · request ${runtimeError.requestId}` : ""}`;
}

function RuntimeCommandCenter() {
  const health = useHealthQuery();
  const agents = useAgentsQuery();
  const scheduler = useSchedulerQuery();
  const hardware = useHardwareQuery();
  const models = useModelsQuery();
  const metrics = useMetricsQuery();
  const { taskId, selectTask } = useSelectedTaskId();
  const selectedTask = useTaskQuery(taskId);
  const createTask = useCreateTaskMutation();
  const cancelTask = useCancelTaskMutation();
  const taskIsTerminal = selectedTask.data ? ["completed", "failed", "cancelled", "timed_out"].includes(selectedTask.data.status) : false;
  const taskEvents = useTaskEvents(taskId, taskIsTerminal);

  const availableModel = models.data?.models.find((model) => model.available) ?? null;
  const ramPercent = percent(hardware.data?.ram.used_mib, hardware.data?.ram.total_mib);
  const vramPercent = percent(hardware.data?.gpu?.used_vram_mib, hardware.data?.gpu?.total_vram_mib);
  const errors = [...new Set(
    [health.error, agents.error, scheduler.error, hardware.error, models.error, metrics.error]
      .map(queryError)
      .filter((error): error is string => error !== null),
  )];

  return (
    <section
      className="runtime-command-center"
      aria-busy={health.isPending || agents.isPending || scheduler.isPending || hardware.isPending || models.isPending || metrics.isPending}
      aria-labelledby="runtime-command-title"
    >
      <div className="runtime-section-heading">
        <div>
          <p className="eyebrow">Live loopback evidence</p>
          <h2 id="runtime-command-title">Runtime pulse</h2>
        </div>
        {health.isPending ? (
          <StatusToken tone="queued">Connecting</StatusToken>
        ) : health.isError ? (
          <StatusToken tone="critical">API unavailable</StatusToken>
        ) : health.data.status === "ok" ? (
          <StatusToken tone="healthy">Runtime live</StatusToken>
        ) : (
          <StatusToken tone="unavailable">Runtime unavailable</StatusToken>
        )}
      </div>

      {errors.length === 0 ? null : (
        <div className="runtime-error" role="alert">
          <strong>Some runtime evidence is unavailable.</strong>
          <ul>{errors.map((error) => <li key={error}>{error}</li>)}</ul>
        </div>
      )}

      <div className="runtime-pulse-grid">
        <EvidenceValue
          label="Runtime"
          value={health.data?.runtime_status ?? (health.isPending ? "Loading" : "Unavailable")}
          detail={health.data?.runtime_name ?? "GET /v1/health"}
        />
        <EvidenceValue
          label="Queue"
          value={scheduler.data ? `${scheduler.data.queue_depth} waiting` : scheduler.isPending ? "Loading" : "Unavailable"}
          detail={scheduler.data ? `${scheduler.data.running}/${scheduler.data.max_workers} workers · ${scheduler.data.policy}` : "GET /v1/scheduler"}
        />
        <EvidenceValue
          label="Selected model"
          value={availableModel?.display_name ?? (models.isPending ? "Loading" : "Unavailable")}
          detail={availableModel ? `${availableModel.quantization} · ${availableModel.latency_class}` : "No available registry model"}
        />
        <EvidenceValue
          label="Host RAM"
          value={formatMemory(hardware.data?.ram.used_mib)}
          detail={hardware.data?.ram.total_mib == null ? "GET /v1/hardware" : `of ${formatMemory(hardware.data.ram.total_mib)} measured`}
          meter={ramPercent}
        />
        <EvidenceValue
          label="GPU VRAM"
          value={formatMemory(hardware.data?.gpu?.used_vram_mib)}
          detail={hardware.data?.gpu?.total_vram_mib == null ? "Unavailable from profiler" : `of ${formatMemory(hardware.data.gpu.total_vram_mib)} · ${formatNumber(hardware.data.gpu.utilization_percent, 0)}% GPU`}
          meter={vramPercent}
        />
        <EvidenceValue
          label="Recent tasks"
          value={metrics.data ? formatNumber(metrics.data.totals.tasks, 0) : metrics.isPending ? "Loading" : "Unavailable"}
          detail={metrics.data?.totals.completion_rate_percent == null ? "No completion-rate sample" : `${formatNumber(metrics.data.totals.completion_rate_percent, 1)}% completed`}
        />
      </div>

      <div className="runtime-foundation-grid">
        <article className="runtime-foundation-panel">
          <div className="panel-title-row">
            <div><p className="eyebrow">Agents</p><h3>Available roles</h3></div>
            <span>{agents.data?.agents.length ?? "—"}</span>
          </div>
          {agents.isPending ? <p className="panel-empty">Loading agent evidence…</p> : null}
          {agents.data?.agents.map((agent) => (
            <div className="agent-row" key={agent.agent_id}>
              <span aria-hidden="true">{agent.name.split(" ").map((word) => word[0]).join("").slice(0, 2)}</span>
              <div><strong>{agent.name}</strong><small>{agent.capabilities.join(" · ")}</small></div>
            </div>
          ))}
        </article>

        <article className="runtime-foundation-panel">
          <div className="panel-title-row">
            <div><p className="eyebrow">Telemetry</p><h3>Current evidence window</h3></div>
            <span>{metrics.data ? "60m" : "—"}</span>
          </div>
          <dl className="telemetry-list">
            <div><dt>Model calls</dt><dd>{metrics.data?.totals.model_calls_completed ?? "—"}</dd></div>
            <div><dt>Trace steps</dt><dd>{metrics.data?.totals.trace_steps ?? "—"}</dd></div>
            <div><dt>Failures</dt><dd>{metrics.data?.totals.failed_tasks ?? "—"}</dd></div>
            <div><dt>Collection</dt><dd>{metrics.data ? `${formatNumber(metrics.data.collection_ms)} ms` : "—"}</dd></div>
          </dl>
        </article>
      </div>

      <div className="runtime-task-grid">
        <TaskComposer
          agents={agents.data?.agents ?? []}
          disabled={createTask.isPending || agents.isPending || agents.isError}
          error={queryError(createTask.error)}
          onSubmit={(input) => createTask.mutate(input, {
            onSuccess: (task) => selectTask(task.task_id),
          })}
          submitting={createTask.isPending}
        />
        {taskId === null ? (
          <article className="task-inspector task-inspector-empty">
            <p className="eyebrow">Selected execution</p>
            <h3>Task evidence</h3>
            <p>Launch a task or open a URL containing <code>?task=&lt;task-id&gt;</code> to inspect its durable state and measured output.</p>
          </article>
        ) : selectedTask.isPending ? (
          <article className="task-inspector task-inspector-empty"><p>Loading task evidence…</p></article>
        ) : selectedTask.isError ? (
          <article className="task-inspector"><div className="runtime-error" role="alert"><strong>Task evidence unavailable.</strong><p>{queryError(selectedTask.error)}</p></div><button type="button" className="quiet-button" onClick={() => selectTask(null)}>Clear selection</button></article>
        ) : (
          <TaskInspector
            task={selectedTask.data}
            cancelling={cancelTask.isPending}
            cancelError={queryError(cancelTask.error)}
            onCancel={() => cancelTask.mutate(selectedTask.data.task_id)}
            onClose={() => selectTask(null)}
          />
        )}
      </div>

      <ExecutionRail events={taskEvents.events} streamState={taskEvents.state} />
    </section>
  );
}

export { RuntimeCommandCenter };
