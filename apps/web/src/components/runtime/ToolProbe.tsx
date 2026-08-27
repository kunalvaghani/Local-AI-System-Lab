import { useMemo, useState } from "react";

import type { AgentSummary, ToolCatalogData } from "../../api/types";
import type { RuntimeApiError } from "../../api/client";
import { useExecuteToolMutation } from "../../query/runtimeQueries";
import { StatusToken } from "../StatusToken";

type ToolProbeProps = {
  agents: AgentSummary[];
  catalog: ToolCatalogData | undefined;
  disabled: boolean;
};

function errorText(error: Error | null) {
  if (!error) return null;
  const runtimeError = error as RuntimeApiError;
  return `${runtimeError.message}${runtimeError.requestId ? ` · request ${runtimeError.requestId}` : ""}`;
}

function ToolProbe({ agents, catalog, disabled }: ToolProbeProps) {
  const [agentChoice, setAgentChoice] = useState("");
  const [toolChoice, setToolChoice] = useState("");
  const [relativePath, setRelativePath] = useState("PROJECT_STATE.md");
  const execute = useExecuteToolMutation();
  const availableTools = catalog?.tools ?? [];
  const authorizedAgents = useMemo(
    () => agents.filter((agent) => availableTools.some((tool) => tool.authorized_agent_ids.includes(agent.agent_id))),
    [agents, availableTools],
  );
  const agentId = authorizedAgents.some((agent) => agent.agent_id === agentChoice)
    ? agentChoice
    : authorizedAgents[0]?.agent_id ?? "";
  const agentTools = availableTools.filter((tool) => tool.authorized_agent_ids.includes(agentId));
  const toolName = agentTools.some((tool) => tool.name === toolChoice)
    ? toolChoice
    : agentTools[0]?.name ?? "";
  const tool = agentTools.find((item) => item.name === toolName) ?? null;
  const needsPath = tool?.arguments.some((argument) => argument.name === "relative_path") ?? false;
  const canRun = !disabled && !execute.isPending && agentId !== "" && tool !== null
    && (!needsPath || relativePath.trim() !== "");
  const failure = errorText(execute.error);
  const content = typeof execute.data?.data.content === "string" ? execute.data.data.content : null;

  return (
    <article className="tool-probe" aria-labelledby="tool-probe-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">Tool boundary</p><h3 id="tool-probe-title">Safe tool probe</h3></div>
        <span>POST /v1/tools/execute</span>
      </div>
      <p className="evidence-note">Runs one server-catalogued, exact-grant, read-only operation through policy, validation, persistence, trace, and telemetry boundaries.</p>
      <form onSubmit={(event) => {
        event.preventDefault();
        if (!canRun || !tool) return;
        const argumentsPayload: Record<string, string | number | boolean> = { max_characters: 1_200 };
        if (needsPath) argumentsPayload.relative_path = relativePath.trim();
        execute.mutate({ agent_id: agentId, tool_name: tool.name, arguments: argumentsPayload });
      }}>
        <label>
          <span>Authorized agent</span>
          <select value={agentId} onChange={(event) => { setAgentChoice(event.target.value); setToolChoice(""); execute.reset(); }} disabled={disabled || authorizedAgents.length === 0}>
            {authorizedAgents.length === 0 ? <option value="">No tool grants available</option> : null}
            {authorizedAgents.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{agent.name}</option>)}
          </select>
        </label>
        <label>
          <span>Registered tool</span>
          <select value={toolName} onChange={(event) => { setToolChoice(event.target.value); execute.reset(); }} disabled={disabled || agentTools.length === 0}>
            {agentTools.map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
          </select>
        </label>
        {needsPath ? (
          <label>
            <span>Project-relative text path</span>
            <input value={relativePath} onChange={(event) => setRelativePath(event.target.value)} maxLength={240} disabled={disabled} />
          </label>
        ) : null}
        <div className="form-actions">
          <span>{tool ? `${tool.timeout_ms} ms ceiling · ${tool.permission.permissions.join(" · ")}` : "Loading catalog"}</span>
          <button type="submit" disabled={!canRun}>{execute.isPending ? "Running…" : "Run bounded tool"}</button>
        </div>
      </form>
      {failure ? <p className="form-error" role="alert">{failure}</p> : null}
      {execute.data ? (
        <div className="tool-result" aria-live="polite">
          <div><StatusToken tone="healthy">Completed</StatusToken><code>{execute.data.task_id}</code></div>
          <dl>
            <div><dt>Tool</dt><dd>{execute.data.tool_name}</dd></div>
            <div><dt>Duration</dt><dd>{execute.data.duration_ms.toFixed(3)} ms</dd></div>
            <div><dt>State</dt><dd>{execute.data.final_state ?? "Unavailable"}</dd></div>
            <div><dt>Trace</dt><dd><a href={`/traces?task=${encodeURIComponent(execute.data.task_id)}`}>Inspect persisted trace</a></dd></div>
          </dl>
          {content ? <pre>{content}</pre> : <pre>{JSON.stringify(execute.data.data, null, 2)}</pre>}
        </div>
      ) : null}
    </article>
  );
}

export { ToolProbe };
