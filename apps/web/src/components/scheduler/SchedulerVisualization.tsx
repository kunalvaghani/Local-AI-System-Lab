import type { SchedulerRequest } from "../../api/types";
import { useSelectedTaskId } from "../../hooks/useSelectedTaskId";
import { useTaskEvents } from "../../hooks/useTaskEvents";
import { useCancelTaskMutation, useSchedulerQuery, useTaskQuery } from "../../query/runtimeQueries";
import { StatusToken, type StatusTone } from "../StatusToken";
import { EvidenceValue } from "../runtime/EvidenceValue";
import { admissionFor, schedulerRequestFor } from "./evidence";
import { AdmissionPanel, SelectedTaskControl, terminalStatuses } from "./SelectedExecution";

const statusTone: Record<SchedulerRequest["status"], StatusTone> = {
  queued: "queued",
  running: "active",
  completed: "healthy",
  cancelled: "warning",
  timed_out: "warning",
  failed: "critical",
};

function formatMs(value: number | null) {
  return value == null ? "Unavailable" : `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value)} ms`;
}

function projectedQueue(requests: SchedulerRequest[], policy: string) {
  const queued = requests.filter((request) => request.status === "queued");
  return [...queued].sort(policy === "priority"
    ? (left, right) => right.effective_priority - left.effective_priority || left.sequence - right.sequence
    : (left, right) => left.sequence - right.sequence);
}

function SchedulerVisualization() {
  const scheduler = useSchedulerQuery();
  const { taskId } = useSelectedTaskId();
  const task = useTaskQuery(taskId);
  const terminal = task.data ? terminalStatuses.has(task.data.status) : false;
  const stream = useTaskEvents(taskId, terminal);
  const cancel = useCancelTaskMutation();
  const data = scheduler.data;
  const running = data?.requests.filter((request) => request.status === "running") ?? [];
  const queue = data ? projectedQueue(data.requests, data.policy) : [];
  const selectedRequest = data?.requests.find((request) => request.task_id === taskId) ?? schedulerRequestFor(task.data);
  const requests = [...(data?.requests ?? [])].sort((left, right) => right.sequence - left.sequence).slice(0, 50);
  const admission = admissionFor(task.data, stream.events);

  return (
    <section className="scheduler-visualization" aria-labelledby="scheduler-map-title">
      <div className="scheduler-section-heading">
        <div>
          <p className="eyebrow">Live dispatch evidence</p>
          <h2 id="scheduler-map-title">Scheduler map</h2>
          <p>Worker occupancy and projected next dispatch derived from the current scheduler snapshot.</p>
        </div>
        {scheduler.isPending ? <StatusToken tone="queued">Loading</StatusToken>
          : scheduler.isError ? <StatusToken tone="critical">Unavailable</StatusToken>
            : <StatusToken tone={data?.running ? "active" : "healthy"}>{data?.running ? "Dispatching" : "Idle"}</StatusToken>}
      </div>

      <div className="scheduler-metric-grid">
        <EvidenceValue label="Policy" value={data?.policy ?? (scheduler.isPending ? "Loading" : "Unavailable")} detail="GET /v1/scheduler" />
        <EvidenceValue label="Workers" value={data ? `${data.running} / ${data.max_workers}` : "Unavailable"} detail="Running / configured" meter={data ? data.running / data.max_workers * 100 : null} />
        <EvidenceValue label="Queue depth" value={data ? String(data.queue_depth) : "Unavailable"} detail={data ? `Peak ${data.peak_queue_depth}` : "No snapshot"} />
        <EvidenceValue label="Queue wait P95" value={data ? formatMs(data.queue_wait_p95_ms) : "Unavailable"} detail="Completed request evidence" />
      </div>

      <div className="dispatch-map">
        <article className="worker-bank">
          <div className="panel-title-row"><div><p className="eyebrow">Capacity</p><h3>Worker slots</h3></div><span>{data?.max_workers ?? "—"}</span></div>
          <ol className="worker-slot-list">
            {Array.from({ length: data?.max_workers ?? 1 }, (_, index) => {
              const request = running[index];
              return (
                <li key={request?.request_id ?? `empty-${index}`} data-occupied={request ? "true" : "false"}>
                  <span>W{index + 1}</span>
                  <div><strong>{request ? request.task_id : "Available"}</strong><small>{request ? `${request.workload} · priority ${request.effective_priority}` : "No active request"}</small></div>
                  <StatusToken tone={request ? "active" : "healthy"}>{request ? "Running" : "Ready"}</StatusToken>
                </li>
              );
            })}
          </ol>
        </article>

        <article className="queue-bank">
          <div className="panel-title-row"><div><p className="eyebrow">Next dispatch</p><h3>Projected queue</h3></div><span>{queue.length}</span></div>
          {queue.length === 0 ? <p className="panel-empty">No requests are waiting in this snapshot.</p> : (
            <ol className="queue-card-list">
              {queue.map((request, index) => (
                <li key={request.request_id}>
                  <span>{index + 1}</span>
                  <div><strong>{request.task_id}</strong><small>{request.workload} · effective priority {request.effective_priority}</small></div>
                  <StatusToken tone={statusTone[request.status]}>{request.status}</StatusToken>
                </li>
              ))}
            </ol>
          )}
          <p className="scheduler-footnote">Projection uses the reported policy, effective priority, and stable sequence. Running work is never presented as preemptible.</p>
        </article>
      </div>

      {taskId === null ? <article className="task-context-empty"><h3>Select a runtime task to inspect its dispatch.</h3><p>The scheduler overview and request ledger remain live. Task-specific admission, placement, timing, and cancellation require a valid <code>?task=</code> selection.</p></article>
        : task.isPending ? <p className="panel-empty">Loading selected task evidence…</p>
          : task.isError || !task.data ? <div className="runtime-error" role="alert">Selected task evidence is unavailable.</div>
            : <>
              <SelectedTaskControl task={task.data} cancelling={cancel.isPending} cancelError={cancel.error?.message ?? null} onCancel={() => cancel.mutate(task.data.task_id)} />
              <div className="scheduler-selected-grid">
                <article className="selected-request-panel">
                  <div className="panel-title-row"><div><p className="eyebrow">Selected dispatch</p><h3>Request placement</h3></div>{selectedRequest ? <StatusToken tone={statusTone[selectedRequest.status]}>{selectedRequest.status}</StatusToken> : <StatusToken tone="unavailable">Not present</StatusToken>}</div>
                  {selectedRequest ? <dl className="admission-evidence-grid">
                    <div><dt>Workload</dt><dd>{selectedRequest.workload}</dd></div>
                    <div><dt>Base priority</dt><dd>{selectedRequest.base_priority}</dd></div>
                    <div><dt>Effective priority</dt><dd>{selectedRequest.effective_priority}</dd></div>
                    <div><dt>Submit position</dt><dd>{selectedRequest.queue_position_at_submit}</dd></div>
                    <div><dt>Queue wait</dt><dd>{formatMs(selectedRequest.queue_wait_ms)}</dd></div>
                    <div><dt>Execution</dt><dd>{formatMs(selectedRequest.execution_ms)}</dd></div>
                    <div><dt>Timeout</dt><dd>{formatMs(selectedRequest.timeout_ms)}</dd></div>
                    <div><dt>Error</dt><dd>{selectedRequest.error_code ?? "None reported"}</dd></div>
                  </dl> : <p className="panel-empty">The selected task is not retained in the current scheduler snapshot.</p>}
                </article>
                <AdmissionPanel admission={admission} />
              </div>
            </>}

      <article className="request-ledger">
        <div className="panel-title-row"><div><p className="eyebrow">Bounded history</p><h3>Request ledger</h3></div><span>{requests.length} / {data?.requests.length ?? 0}</span></div>
        {requests.length === 0 ? <p className="panel-empty">No scheduler requests have been reported in this process.</p> : (
          <div className="request-table-scroll"><table><thead><tr><th scope="col">Sequence</th><th scope="col">Task</th><th scope="col">State</th><th scope="col">Workload</th><th scope="col">Priority</th><th scope="col">Queue wait</th><th scope="col">Execution</th></tr></thead>
            <tbody>{requests.map((request) => <tr data-selected={request.task_id === taskId ? "true" : "false"} key={request.request_id}><td>{request.sequence}</td><td><code>{request.task_id}</code></td><td><StatusToken tone={statusTone[request.status]}>{request.status}</StatusToken></td><td>{request.workload}</td><td>{request.base_priority} → {request.effective_priority}</td><td>{formatMs(request.queue_wait_ms)}</td><td>{formatMs(request.execution_ms)}</td></tr>)}</tbody></table></div>
        )}
        <p className="scheduler-footnote">Latest 50 requests by sequence. Values are scheduler snapshots; no queue positions or timings are synthesized by the interface.</p>
      </article>
    </section>
  );
}

export { SchedulerVisualization };
