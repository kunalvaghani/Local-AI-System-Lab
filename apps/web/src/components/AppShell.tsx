import { Group, Panel, Separator } from "react-resizable-panels";

import { useDensity } from "../hooks/useDensity";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { useRoute } from "../navigation/useRoute";
import { DomainRail } from "./DomainRail";
import { EvidencePane } from "./EvidencePane";
import { RouteWorkspace } from "./RouteWorkspace";
import { SystemBar } from "./SystemBar";

function AppShell() {
  const { activePath, activeRoute, navigate, routeHref } = useRoute();
  const { density, setDensity } = useDensity();
  const stackedInspector = useMediaQuery("(max-width: 68.75rem)");

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-workspace">Skip to workspace</a>
      <SystemBar density={density} onDensityChange={setDensity} />
      <DomainRail activePath={activePath} onNavigate={navigate} routeHref={routeHref} />

      <Group
        className="inspector-frame"
        defaultLayout={stackedInspector ? { workspace: 68, evidence: 32 } : { workspace: 76, evidence: 24 }}
        id="runtime-inspector"
        orientation={stackedInspector ? "vertical" : "horizontal"}
        resizeTargetMinimumSize={{ coarse: 36, fine: 16 }}
      >
        <Panel id="workspace" minSize="55%">
          <RouteWorkspace route={activeRoute} />
        </Panel>
        <Separator className="pane-separator" id="workspace-evidence-separator">
          <span aria-hidden="true" />
        </Separator>
        <Panel id="evidence" minSize="16rem" maxSize="45%">
          <EvidencePane route={activeRoute} />
        </Panel>
      </Group>
    </div>
  );
}

export { AppShell };
