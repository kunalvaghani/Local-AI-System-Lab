import type { RouteDefinition } from "../navigation/routes";
import { DesignSystemView } from "./DesignSystemView";
import { RuntimeCommandCenter } from "./runtime/RuntimeCommandCenter";
import { StatusToken } from "./StatusToken";

type RouteWorkspaceProps = {
  route: RouteDefinition;
};

function RouteWorkspace({ route }: RouteWorkspaceProps) {
  return (
    <main className="workspace" id="main-workspace" tabIndex={-1}>
      <div className="route-heading">
        <div>
          <p className="eyebrow">{route.group} / {route.shortLabel}</p>
          <h1>{route.label}</h1>
          <p>{route.purpose}</p>
        </div>
        <span className="route-endpoint">{route.endpoint}</span>
      </div>

      {route.path === "/runtime" ? (
        <RuntimeCommandCenter />
      ) : route.path === "/design-system" ? (
        <DesignSystemView />
      ) : (
        <section className="empty-surface" aria-labelledby="surface-title">
          <div className="contour" aria-hidden="true"><span /><span /><span /></div>
          <p className="eyebrow">Stage boundary</p>
          <h2 id="surface-title">Interface contract ready</h2>
          <p>
            This workspace intentionally contains no simulated runtime values. Stage 19 will
            connect this surface to the documented loopback API.
          </p>
          <dl>
            <div><dt>Route</dt><dd>{route.path}</dd></div>
            <div><dt>Evidence source</dt><dd>{route.endpoint}</dd></div>
            <div><dt>Data state</dt><dd><StatusToken tone="unavailable">Not requested</StatusToken></dd></div>
          </dl>
        </section>
      )}
    </main>
  );
}

export { RouteWorkspace };
