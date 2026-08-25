import type { RouteDefinition } from "../navigation/routes";

type EvidencePaneProps = {
  route: RouteDefinition;
};

function EvidencePane({ route }: EvidencePaneProps) {
  return (
    <aside className="evidence-pane" aria-labelledby="evidence-title">
      <p className="eyebrow">Context / {route.shortLabel}</p>
      <h2 id="evidence-title">Evidence boundary</h2>
      <p>Values appear here only after a real API response, retained result, or measured browser event exists.</p>
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
    </aside>
  );
}

export { EvidencePane };
