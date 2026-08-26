import { useState } from "react";

import type { AgentSummary, CreateTaskInput, Workload } from "../../api/types";

type TaskComposerProps = {
  agents: AgentSummary[];
  disabled: boolean;
  error: string | null;
  onSubmit: (input: CreateTaskInput) => void;
  submitting: boolean;
};

const workloadDetails: Record<Workload, string> = {
  interactive: "Lowest queue latency",
  standard: "Balanced scheduling",
  background: "Yield to active work",
};

function TaskComposer({ agents, disabled, error, onSubmit, submitting }: TaskComposerProps) {
  const [agentId, setAgentId] = useState("");
  const [objective, setObjective] = useState("");
  const [workload, setWorkload] = useState<Workload>("interactive");

  const selectedAgentId = agents.some((agent) => agent.agent_id === agentId)
    ? agentId
    : agents[0]?.agent_id ?? "";
  const canSubmit = !disabled && selectedAgentId !== "" && objective.trim().length >= 3;

  return (
    <article className="task-composer">
      <div className="panel-title-row">
        <div><p className="eyebrow">Command</p><h3>Launch a bounded task</h3></div>
        <span>POST /v1/tasks</span>
      </div>
      <form onSubmit={(event) => {
        event.preventDefault();
        if (!canSubmit) return;
        onSubmit({ agent_id: selectedAgentId, objective: objective.trim(), workload, timeout_ms: 30_000 });
      }}>
        <label>
          <span>Agent</span>
          <select value={selectedAgentId} onChange={(event) => setAgentId(event.target.value)} disabled={disabled || agents.length === 0}>
            {agents.length === 0 ? <option value="">No agents available</option> : null}
            {agents.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{agent.name}</option>)}
          </select>
        </label>
        <label>
          <span>Objective</span>
          <textarea
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            maxLength={4_096}
            rows={4}
            placeholder="Describe one concrete, inspectable objective…"
            disabled={disabled}
          />
          <small>{objective.length.toLocaleString()} / 4,096 characters</small>
        </label>
        <fieldset>
          <legend>Workload class</legend>
          <div className="workload-options">
            {(Object.keys(workloadDetails) as Workload[]).map((value) => (
              <label key={value}>
                <input type="radio" name="workload" value={value} checked={workload === value} onChange={() => setWorkload(value)} disabled={disabled} />
                <span><strong>{value}</strong><small>{workloadDetails[value]}</small></span>
              </label>
            ))}
          </div>
        </fieldset>
        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <div className="form-actions">
          <span>30 s execution limit</span>
          <button type="submit" disabled={!canSubmit}>{submitting ? "Submitting…" : "Launch task"}</button>
        </div>
      </form>
    </article>
  );
}

export { TaskComposer };
