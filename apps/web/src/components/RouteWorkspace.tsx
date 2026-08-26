import type { RouteDefinition } from "../navigation/routes";
import type { Ref } from "react";
import { DesignSystemView } from "./DesignSystemView";
import { ChaosSecurityLab } from "./chaos/ChaosSecurityLab";
import { PerformanceLab } from "./performance/PerformanceLab";
import { RuntimeCommandCenter } from "./runtime/RuntimeCommandCenter";
import { AgentVisualization } from "./scheduler/AgentVisualization";
import { SchedulerVisualization } from "./scheduler/SchedulerVisualization";
import { StatusToken } from "./StatusToken";
import { TraceExplorer } from "./trace/TraceExplorer";

type RouteWorkspaceProps = {
  ref?: Ref<HTMLElement>;
  route: RouteDefinition;
};

function RouteWorkspace({ ref, route }: RouteWorkspaceProps) {
  return (
    <main className="workspace" id="main-workspace" ref={ref} tabIndex={-1}>
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
      ) : route.path === "/agents" ? (
        <AgentVisualization />
      ) : route.path === "/scheduler" ? (
        <SchedulerVisualization />
      ) : route.path === "/traces" ? (
        <TraceExplorer />
      ) : route.path === "/hardware" || route.path === "/metrics" ? (
        <PerformanceLab focus={route.path === "/hardware" ? "hardware" : "metrics"} />
      ) : route.path === "/chaos" || route.path === "/security" ? (
        <ChaosSecurityLab focus={route.path === "/chaos" ? "chaos" : "security"} />
      ) : route.path === "/design-system" ? (
        <DesignSystemView />
      ) : (
        <section className="empty-surface" aria-labelledby="surface-title">
          <div className="contour" aria-hidden="true"><span /><span /><span /></div>
          <p className="eyebrow">Stage boundary</p>
          <h2 id="surface-title">Interface contract ready</h2>
          <p>
            This workspace intentionally contains no simulated runtime values. Its stage will
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
