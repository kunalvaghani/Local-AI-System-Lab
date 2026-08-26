import { Group, Panel, Separator, useGroupRef } from "react-resizable-panels";
import { useRef, useState } from "react";

import { useDensity } from "../hooks/useDensity";
import { useMediaQuery } from "../hooks/useMediaQuery";
import { useRoute } from "../navigation/useRoute";
import { DomainRail } from "./DomainRail";
import { EvidencePane } from "./EvidencePane";
import { RouteWorkspace } from "./RouteWorkspace";
import { SystemBar } from "./SystemBar";
import { CommandPalette } from "./interaction/CommandPalette";

const STACKED_LAYOUT = { workspace: 68, evidence: 32 };
const WIDE_LAYOUT = { workspace: 76, evidence: 24 };

function AppShell() {
  const { activePath, activeRoute, navigate, navigateTo, routeHref } = useRoute();
  const { density, setDensity } = useDensity();
  const stackedInspector = useMediaQuery("(max-width: 68.75rem)");
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const commandTriggerRef = useRef<HTMLButtonElement>(null);
  const workspaceRef = useRef<HTMLElement>(null);
  const inspectorRef = useGroupRef();
  const defaultLayout = stackedInspector ? STACKED_LAYOUT : WIDE_LAYOUT;

  function setCommandPaletteState(nextOpen: boolean) {
    setCommandPaletteOpen(nextOpen);
    if (!nextOpen) {
      window.setTimeout(() => commandTriggerRef.current?.focus({ preventScroll: true }), 0);
    }
  }

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-workspace"
        onClick={(event) => {
          event.preventDefault();
          window.setTimeout(() => {
            workspaceRef.current?.focus();
          }, 0);
        }}
      >
        Skip to workspace
      </a>
      <SystemBar
        commandTriggerRef={commandTriggerRef}
        density={density}
        onCommandPaletteOpen={() => setCommandPaletteState(true)}
        onDensityChange={setDensity}
      />
      <DomainRail activePath={activePath} onNavigate={navigate} routeHref={routeHref} />

      <CommandPalette
        activePath={activePath}
        isOpen={commandPaletteOpen}
        onNavigate={navigateTo}
        onOpenChange={setCommandPaletteState}
        routeHref={routeHref}
      />

      <Group
        className="inspector-frame"
        defaultLayout={defaultLayout}
        groupRef={inspectorRef}
        id="runtime-inspector"
        orientation={stackedInspector ? "vertical" : "horizontal"}
        resizeTargetMinimumSize={{ coarse: 36, fine: 16 }}
      >
        <Panel id="workspace" minSize="55%">
          <RouteWorkspace ref={workspaceRef} route={activeRoute} />
        </Panel>
        <Separator className="pane-separator" id="workspace-evidence-separator">
          <span aria-hidden="true" />
        </Separator>
        <Panel id="evidence" minSize="16rem" maxSize="45%">
          <EvidencePane
            onResetLayout={() => inspectorRef.current?.setLayout(defaultLayout)}
            route={activeRoute}
          />
        </Panel>
      </Group>
    </div>
  );
}

export { AppShell };
