import { Tab, TabList, TabPanel, Tabs } from "react-aria-components/Tabs";

import { StatusToken } from "./StatusToken";

const statusExamples = [
  ["healthy", "Healthy"],
  ["active", "Running"],
  ["queued", "Queued"],
  ["warning", "Pressure"],
  ["critical", "Failed"],
  ["blocked", "Blocked"],
  ["partial", "Partial"],
  ["deferred", "Deferred"],
  ["unavailable", "Unavailable"],
  ["stale", "Stale"],
  ["unknown", "Unknown"],
] as const;

function DesignSystemView() {
  return (
    <section className="design-system" aria-labelledby="design-system-title">
      <div className="section-heading">
        <p className="eyebrow">Interactive foundation</p>
        <h2 id="design-system-title">Systems Cartography language</h2>
        <p>Operational hierarchy, evidence-first state, and compact inspection without decorative telemetry.</p>
      </div>

      <Tabs aria-label="Design system foundations" className="prototype-tabs">
        <TabList>
          <Tab id="foundations">Foundations</Tab>
          <Tab id="states">States</Tab>
          <Tab id="visualization">Visualization</Tab>
        </TabList>

        <TabPanel id="foundations">
          <div className="foundation-grid">
            <article className="foundation-card">
              <span className="sample-display">Aa</span>
              <h3>Operational typography</h3>
              <p>Humanist system UI for reading; tabular monospace for identifiers, values, and evidence.</p>
            </article>
            <article className="foundation-card">
              <span className="sample-spacing" aria-hidden="true"><i /><i /><i /><i /></span>
              <h3>Four-pixel rhythm</h3>
              <p>Seven spacing steps scale from dense controls to route-level separation.</p>
            </article>
            <article className="foundation-card">
              <span className="sample-surface" aria-hidden="true"><i /><i /><i /></span>
              <h3>Evidence surfaces</h3>
              <p>Depth comes from borders and luminance; shadow is reserved for raised temporary context.</p>
            </article>
          </div>
        </TabPanel>

        <TabPanel id="states">
          <p className="panel-intro">Every state combines a label, glyph, and controlled tone. Color never carries meaning alone.</p>
          <div className="status-grid">
            {statusExamples.map(([tone, label]) => (
              <StatusToken key={tone} tone={tone}>{label}</StatusToken>
            ))}
          </div>
        </TabPanel>

        <TabPanel id="visualization">
          <div className="visualization-contract">
            <div className="duration-bars" aria-hidden="true">
              <span style={{ "--duration": "72%" } as React.CSSProperties} />
              <span style={{ "--duration": "43%" } as React.CSSProperties} />
              <span style={{ "--duration": "21%" } as React.CSSProperties} />
            </div>
            <div>
              <h3>Truth before spectacle</h3>
              <p>Charts require units, source, time window, numeric alternatives, bounded points, and explicit missing/stale states.</p>
            </div>
          </div>
        </TabPanel>
      </Tabs>
    </section>
  );
}

export { DesignSystemView };
