import { ToggleButton, ToggleButtonGroup } from "react-aria-components/ToggleButtonGroup";

import type { Density } from "../hooks/useDensity";
import { useHealthQuery } from "../query/runtimeQueries";
import { StatusToken } from "./StatusToken";

type SystemBarProps = {
  density: Density;
  onDensityChange: (density: Density) => void;
};

function SystemBar({ density, onDensityChange }: SystemBarProps) {
  const health = useHealthQuery();

  return (
    <header className="system-bar">
      <div className="brand-lockup" aria-label="Local AI Systems Lab">
        <span className="brand-mark" aria-hidden="true">LA</span>
        <span>
          <strong>Local AI</strong>
          <small>Systems Lab / Stage 21</small>
        </span>
      </div>

      <div className="system-controls">
        <ToggleButtonGroup
          aria-label="Interface density"
          className="density-control"
          onSelectionChange={(keys) => {
            const next = [...keys][0];
            if (next === "comfortable" || next === "compact") {
              onDensityChange(next);
            }
          }}
          selectedKeys={[density]}
          selectionMode="single"
          disallowEmptySelection
        >
          <ToggleButton id="comfortable">Comfort</ToggleButton>
          <ToggleButton id="compact">Compact</ToggleButton>
        </ToggleButtonGroup>

        <div className="connection-state">
          {health.isPending ? (
            <StatusToken tone="queued">Connecting</StatusToken>
          ) : health.isError ? (
            <StatusToken tone="critical">API unavailable</StatusToken>
          ) : health.data.status === "ok" ? (
            <StatusToken tone="healthy">API live</StatusToken>
          ) : (
            <StatusToken tone="unavailable">API unavailable</StatusToken>
          )}
          <small>{health.data?.runtime_name ?? "/v1/health"}</small>
        </div>
      </div>
    </header>
  );
}

export { SystemBar };
