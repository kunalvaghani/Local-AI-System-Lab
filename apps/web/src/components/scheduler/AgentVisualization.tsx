import type { LifecycleEventData, StateHistoryItem } from "../../api/types";
import { useSelectedTaskId } from "../../hooks/useSelectedTaskId";
import { useTaskEvents } from "../../hooks/useTaskEvents";
import { useAgentsQuery, useCancelTaskMutation, useSchedulerQuery, useTaskQuery } from "../../query/runtimeQueries";
import { StatusToken } from "../StatusToken";
import { admissionFor, schedulerRequestFor } from "./evidence";
import { AdmissionPanel, SelectedTaskControl, terminalStatuses } from "./SelectedExecution";

function statePath(task: ReturnType<typeof useTaskQuery>["data"], events: ReturnType<typeof useTaskEvents>["events"]): StateHistoryItem[] {
  if (task?.result?.state_history.length) return task.result.state_history;
  const live = events.flatMap((event, index) => {
    if (event.event !== "lifecycle") return [];
    const item = event.data as LifecycleEventData;
    return item.state ? [{ sequence: Number(event.id) || index + 1, from_state: null, to_state: item.state, reason: item.name, recorded_at_utc: item.recorded_at_utc }] : [];
  });
  const deduped = live.filter((item, index) => index === 0 || item.to_state !== live[index - 1].to_state);
  if (deduped.length || !task?.durable_state) return deduped;
  return [{ sequence: 1, from_state: null, to_state: task.durable_state, reason: "Current durable task snapshot", recorded_at_utc: task.started_at_utc ?? task.accepted_at_utc }];
}

function AgentVisualization() {
  const agents = useAgentsQuery();
  const scheduler = useSchedulerQuery();
  const { taskId } = useSelectedTaskId();
  const task = useTaskQuery(taskId);
  const terminal = task.data ? terminalStatuses.has(task.data.status) : false;
  const stream = useTaskEvents(taskId, terminal);
  const cancel = useCancelTaskMutation();
  const selectedAgent = agents.data?.agents.find((agent) => agent.agent_id === task.data?.agent_id);
  const request = scheduler.data?.requests.find((item) => item.task_id === taskId) ?? schedulerRequestFor(task.data);
  const states = statePath(task.data, stream.events);
  const admission = admissionFor(task.data, stream.events);

  return (
    <section className="agent-visualization" aria-labelledby="agent-map-title">
      <div className="scheduler-section-heading">
        <div><p className="eyebrow">Registered roles + selected execution</p><h2 id="agent-map-title">Agent state map</h2><p>Who can act, which role owns the selected task, and how its durable state advances.</p></div>
        <StatusToken tone={stream.state === "live" ? "active" : agents.isError ? "critical" : "healthy"}>{stream.state === "live" ? "Following live" : agents.isError ? "Unavailable" : "Catalog live"}</StatusToken>
      </div>

      <div className="agent-catalog">
        {agents.isPending ? <p className="panel-empty">Loading registered agents…</p> : null}
        {agents.data?.agents.map((agent) => (
          <article className="agent-card" data-selected={agent.agent_id === task.data?.agent_id ? "true" : "false"} key={agent.agent_id}>
            <div className="panel-title-row"><div><p className="eyebrow">{agent.agent_id}</p><h3>{agent.name}</h3></div>{agent.agent_id === task.data?.agent_id ? <StatusToken tone="active">Selected</StatusToken> : null}</div>
            <p>{agent.objective}</p>
            <dl><div><dt>Capabilities</dt><dd>{agent.capabilities.join(" · ") || "None reported"}</dd></div><div><dt>Tools</dt><dd>{agent.tools.length ? agent.tools.map((tool) => `${tool.name} [${tool.permissions.join(", ") || "no permissions"}]`).join(" · ") : "None registered"}</dd></div></dl>
          </article>
        ))}
      </div>

      {taskId === null ? <article className="task-context-empty"><h3>Select a runtime task to reveal its execution graph.</h3><p>The agent catalog above is live. Task-specific states, admission, scheduler placement, and cancellation appear when the URL contains a valid <code>?task=</code> selection.</p></article>
        : task.isPending ? <p className="panel-empty">Loading selected task evidence…</p>
          : task.isError || !task.data ? <div className="runtime-error" role="alert">Selected task evidence is unavailable.</div>
            : <>
              <SelectedTaskControl task={task.data} cancelling={cancel.isPending} cancelError={cancel.error?.message ?? null} onCancel={() => cancel.mutate(task.data.task_id)} />
              <div className="execution-map-grid">
                <article className="state-path-panel">
                  <div className="panel-title-row"><div><p className="eyebrow">Durable state machine</p><h3>State path</h3></div><span>{states.length}</span></div>
                  {states.length ? <ol className="state-path">{states.map((state) => <li key={`${state.sequence}-${state.to_state}`}><span aria-hidden="true" /><div><strong>{state.to_state}</strong><small>{state.reason}</small></div><time>{new Date(state.recorded_at_utc).toLocaleTimeString()}</time></li>)}</ol> : <p className="panel-empty">No state transition has been reported yet.</p>}
                </article>
                <article className="execution-flow-panel">
                  <div className="panel-title-row"><div><p className="eyebrow">Cross-component handoff</p><h3>Execution flow</h3></div><span>5 steps</span></div>
                  <ol className="execution-flow">
                    <li><span>01</span><div><strong>Task intake</strong><small>{task.data.status} · {task.data.durable_state ?? "state pending"}</small></div></li>
                    <li><span>02</span><div><strong>Agent owner</strong><small>{selectedAgent?.name ?? task.data.agent_id}</small></div></li>
                    <li><span>03</span><div><strong>Resource admission</strong><small>{admission ? `${admission.action} · ${admission.permitted ? "permitted" : "blocked"}` : "not yet reported"}</small></div></li>
                    <li><span>04</span><div><strong>Scheduler</strong><small>{request ? `${request.status} · ${request.workload} · priority ${request.effective_priority}` : "request not in current snapshot"}</small></div></li>
                    <li><span>05</span><div><strong>Outcome</strong><small>{task.data.result?.final_state ?? (terminal ? task.data.status : "pending")}</small></div></li>
                  </ol>
                </article>
              </div>
              <AdmissionPanel admission={admission} />
            </>}
    </section>
  );
}

export { AgentVisualization };
