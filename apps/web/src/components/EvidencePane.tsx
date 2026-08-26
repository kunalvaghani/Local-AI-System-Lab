import type { RouteDefinition } from "../navigation/routes";
import { useSelectedTaskId } from "../hooks/useSelectedTaskId";
import { StatusToken } from "./StatusToken";

type EvidencePaneProps = {
  onResetLayout: () => void;
  route: RouteDefinition;
};

function EvidencePane({ onResetLayout, route }: EvidencePaneProps) {
  const { taskId } = useSelectedTaskId();

  return (
    <aside className="evidence-pane" aria-labelledby="evidence-title">
      <p className="eyebrow">Context / {route.shortLabel}</p>
      <div className="context-heading">
        <h2 id="evidence-title">Evidence boundary</h2>
        <StatusToken tone={taskId ? "active" : "unavailable"}>
          {taskId ? "Task scoped" : "Workspace"}
        </StatusToken>
      </div>
      <p>Values appear here only after a real API response, retained result, or measured browser event exists.</p>
      <dl className="context-facts" aria-label="Current workspace context">
        <div><dt>Domain</dt><dd>{route.group}</dd></div>
        <div><dt>Route</dt><dd>{route.path}</dd></div>
        <div><dt>Task</dt><dd>{taskId ?? "No task selected"}</dd></div>
      </dl>
      <ol className="evidence-path">
        <li><span>01</span> Request</li>
        <li><span>02</span> Runtime</li>
        <li><span>03</span> Evidence</li>
        <li><span>04</span> View</li>
      </ol>
      <div className="pane-note">
        <span>Source contract</span>
        <code>{route.endpoint}</code>
      </div>
      <details className="context-disclosure">
        <summary>Interaction map</summary>
        <ul>
          <li><kbd>Ctrl K</kbd> or <kbd>/</kbd> opens workspace navigation.</li>
          <li>Arrow keys resize the focused pane separator.</li>
          <li>Route changes retain a validated selected task.</li>
        </ul>
        <button type="button" onClick={onResetLayout}>Reset pane split</button>
      </details>
    </aside>
  );
}

export { EvidencePane };
