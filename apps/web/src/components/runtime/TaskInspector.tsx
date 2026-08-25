import type { TaskRecord } from "../../api/types";
import { StatusToken, type StatusTone } from "../StatusToken";
import { EvidenceValue } from "./EvidenceValue";

type TaskInspectorProps = {
  task: TaskRecord;
  cancelling: boolean;
  cancelError: string | null;
  onCancel: () => void;
  onClose: () => void;
};

const terminal = new Set(["completed", "failed", "cancelled", "timed_out"]);
const taskTone: Record<TaskRecord["status"], StatusTone> = {
  accepted: "queued",
  running: "active",
  completed: "healthy",
  failed: "critical",
  cancelled: "warning",
  timed_out: "warning",
};

function metric(value: number | null | undefined, unit: string) {
  return value == null ? "Unavailable" : `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(value)} ${unit}`;
}

function TaskInspector({ task, cancelling, cancelError, onCancel, onClose }: TaskInspectorProps) {
  const inference = task.result?.inference_metrics;
  return (
    <article className="task-inspector" aria-labelledby="task-inspector-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">Selected execution</p><h3 id="task-inspector-title">Task evidence</h3></div>
        <StatusToken tone={taskTone[task.status]}>{task.status}</StatusToken>
      </div>
      <div className="task-id-row"><code>{task.task_id}</code><button type="button" className="quiet-button" onClick={onClose}>Clear</button></div>
      <p className="task-objective">{task.objective}</p>
      <div className="task-evidence-grid">
        <EvidenceValue label="Durable state" value={task.durable_state ?? "Unavailable"} detail={task.agent_id} />
        <EvidenceValue label="Total inference" value={metric(inference?.total_ms, "ms")} detail={task.result?.backend_name ?? "No backend evidence"} />
        <EvidenceValue label="First token" value={metric(inference?.ttft_ms, "ms")} detail={task.result?.model_id ?? "No model evidence"} />
        <EvidenceValue label="Throughput" value={metric(inference?.tokens_per_second, "tok/s")} detail={inference?.generated_token_runs == null ? "No generated-token sample" : `${inference.generated_token_runs} measured run(s)`} />
      </div>
      {task.result?.output ? <div className="task-output"><p className="eyebrow">Runtime output</p><pre>{task.result.output}</pre></div> : null}
      {task.error ? <div className="runtime-error" role="alert"><strong>{task.error.code}</strong><p>{task.error.message}</p></div> : null}
      {cancelError ? <p className="form-error" role="alert">{cancelError}</p> : null}
      {!terminal.has(task.status) ? <button className="danger-button" type="button" onClick={onCancel} disabled={cancelling || task.cancellation_requested}>{task.cancellation_requested ? "Cancellation requested" : cancelling ? "Requesting cancellation…" : "Cancel task"}</button> : null}
    </article>
  );
}

export { TaskInspector };
