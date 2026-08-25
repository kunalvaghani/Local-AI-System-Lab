import type { AdmissionEvidence } from "./evidence";
import type { TaskRecord } from "../../api/types";
import { StatusToken } from "../StatusToken";

const terminalStatuses = new Set(["completed", "failed", "cancelled", "timed_out"]);

type SelectedTaskControlProps = {
  task: TaskRecord;
  cancelling: boolean;
  cancelError: string | null;
  onCancel: () => void;
};

function SelectedTaskControl({ task, cancelling, cancelError, onCancel }: SelectedTaskControlProps) {
  const terminal = terminalStatuses.has(task.status);
  return (
    <div className="selected-task-control">
      <div>
        <p className="eyebrow">Selected execution</p>
        <code>{task.task_id}</code>
        <strong>{task.objective}</strong>
      </div>
      <StatusToken tone={task.status === "running" ? "active" : task.status === "completed" ? "healthy" : task.status === "accepted" ? "queued" : "warning"}>{task.status}</StatusToken>
      {terminal ? null : (
        <button className="danger-button" disabled={cancelling || task.cancellation_requested} onClick={onCancel} type="button">
          {task.cancellation_requested ? "Cancellation requested" : cancelling ? "Requesting cancellation…" : "Cancel task"}
        </button>
      )}
      {cancelError ? <p className="form-error" role="alert">{cancelError}</p> : null}
    </div>
  );
}

function AdmissionPanel({ admission }: { admission: AdmissionEvidence | null }) {
  return (
    <article className="admission-panel">
      <div className="panel-title-row">
        <div><p className="eyebrow">Resource gate</p><h3>Admission decision</h3></div>
        {admission ? <StatusToken tone={admission.permitted ? "healthy" : "blocked"}>{admission.action}</StatusToken> : <StatusToken tone="unavailable">Not reported</StatusToken>}
      </div>
      {admission ? (
        <>
          <p>{admission.reason}</p>
          <dl className="admission-evidence-grid">
            <div><dt>Confidence</dt><dd>{admission.confidence}</dd></div>
            <div><dt>Model</dt><dd>{admission.estimate?.model_id ?? admission.fallback_model_id ?? "Unavailable"}</dd></div>
            <div><dt>Context</dt><dd>{admission.estimate ? admission.estimate.context_tokens.toLocaleString() : "Unavailable"}</dd></div>
            <div><dt>GPU layers</dt><dd>{admission.estimate?.gpu_layers ?? "Unavailable"}</dd></div>
            <div><dt>Predicted RAM</dt><dd>{admission.estimate ? `${admission.estimate.predicted_host_ram_mib.toLocaleString()} MiB` : "Unavailable"}</dd></div>
            <div><dt>Predicted VRAM</dt><dd>{admission.estimate ? `${admission.estimate.predicted_vram_mib.toLocaleString()} MiB` : "Unavailable"}</dd></div>
          </dl>
          {admission.constraints.length ? <p className="scheduler-footnote">Constraints: {admission.constraints.join(" · ")}</p> : null}
        </>
      ) : <p className="panel-empty">No admission decision exists in the selected task snapshot or live lifecycle stream yet.</p>}
    </article>
  );
}

export { AdmissionPanel, SelectedTaskControl, terminalStatuses };
