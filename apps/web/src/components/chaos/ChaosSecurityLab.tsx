import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { RuntimeApiError, runtimeApi } from "../../api/client";
import type { ChaosScenarioResult, SecurityCaseResult, SecurityResultsData } from "../../api/types";
import { StatusToken } from "../StatusToken";

type ChaosSecurityLabProps = { focus: "chaos" | "security" };

function errorMessage(error: unknown) {
  return error instanceof RuntimeApiError
    ? `${error.message}${error.requestId ? ` · request ${error.requestId}` : ""}`
    : "Runtime evidence is unavailable.";
}

function formatNumber(value: number | null, digits = 1) {
  return value == null ? "Unavailable" : new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(value);
}

function EvidenceMetric({ label, value, detail }: { label: string; value: React.ReactNode; detail: string }) {
  return (
    <div className="experiment-metric">
      <dt>{label}</dt>
      <dd><span>{value}</span><small>{detail}</small></dd>
    </div>
  );
}

function primitiveEvidence(value: unknown): string {
  if (value == null) return "unavailable";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(primitiveEvidence).join(" → ");
  return JSON.stringify(value);
}

function ChaosOutcome({ outcome }: { outcome: ChaosScenarioResult }) {
  const recovery = outcome.recovery.attempted
    ? outcome.recovery.succeeded === true ? "Recovered" : outcome.recovery.succeeded === false ? "Recovery failed" : "Recovery unavailable"
    : "Not applicable";
  const details = Object.entries(outcome.details).filter(([, value]) => value != null).slice(0, 6);

  return (
    <li className="propagation-card">
      <div className="propagation-title">
        <div><strong>{outcome.scenario_id}</strong><small>{outcome.kind} · {outcome.target}</small></div>
        <StatusToken tone={outcome.expected_outcome_met ? "healthy" : "critical"}>
          {outcome.expected_outcome_met ? "Expected outcome" : "Mismatch"}
        </StatusToken>
      </div>
      <div className="propagation-path" aria-label={`Failure propagation for ${outcome.scenario_id}`}>
        <span><small>Injected</small><strong>{outcome.injected ? `${outcome.injection_count} occurrence` : "No"}</strong></span>
        <i aria-hidden="true">→</i>
        <span><small>Expected</small><strong>{outcome.expected.state ?? "No state"}</strong><em>{outcome.expected.error_code ?? "No error"}</em></span>
        <i aria-hidden="true">→</i>
        <span><small>Actual</small><strong>{outcome.actual.state ?? "No state"}</strong><em>{outcome.actual.error_code ?? "No error"}</em></span>
        <i aria-hidden="true">→</i>
        <span><small>Boundary</small><strong>{outcome.contained ? "Contained" : "Escaped"}</strong><em>{recovery}</em></span>
      </div>
      <dl className="outcome-metrics">
        <div><dt>Duration</dt><dd>{formatNumber(outcome.duration_ms)} ms</dd></div>
        <div><dt>Added latency</dt><dd>{formatNumber(outcome.added_latency_ms)} ms</dd></div>
        <div><dt>Trace steps</dt><dd>{outcome.trace_steps}</dd></div>
        <div><dt>Task</dt><dd>{outcome.task_id ?? "Unavailable"}</dd></div>
      </dl>
      {details.length ? (
        <details>
          <summary>Recovery and propagation evidence</summary>
          <dl className="evidence-list">{details.map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{primitiveEvidence(value)}</dd></div>)}</dl>
        </details>
      ) : null}
    </li>
  );
}

function ChaosWorkspace() {
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const catalog = useQuery({ queryKey: ["chaos-catalog"], queryFn: ({ signal }) => runtimeApi.chaosCatalog(signal) });
  const run = useMutation({ mutationFn: (scenarios: string[]) => runtimeApi.runChaos(scenarios) });
  const maximum = catalog.data?.maximum_scenarios_per_run ?? 0;
  const summary = run.data?.report.summary;

  const toggle = (scenarioId: string) => {
    setSelected((current) => current.includes(scenarioId)
      ? current.filter((item) => item !== scenarioId)
      : current.length < maximum ? [...current, scenarioId] : current);
  };

  return (
    <section className="experiment-lab" aria-labelledby="experiment-title">
      <header className="experiment-heading">
        <div>
          <p className="eyebrow">Controlled reliability experiment</p>
          <h2 id="experiment-title">Chaos lab</h2>
          <p>Select server-reported faults, confirm isolation, and inspect how typed failures propagate, remain contained, and recover.</p>
        </div>
        <StatusToken tone={run.isPending ? "active" : catalog.data?.armed_by_default ? "critical" : "healthy"}>
          {run.isPending ? "Experiment running" : catalog.data?.armed_by_default ? "Armed by default" : "Disarmed by default"}
        </StatusToken>
      </header>

      {catalog.isError ? <div className="experiment-alert" role="alert">{errorMessage(catalog.error)}</div> : null}
      <form className="scenario-console" onSubmit={(event) => { event.preventDefault(); run.mutate(selected); }}>
        <fieldset disabled={catalog.isPending || run.isPending}>
          <legend>Fault scenarios <span>{selected.length}/{maximum || "—"} selected</span></legend>
          <p className="experiment-boundary">{catalog.data?.isolation ?? "Loading isolation contract…"}</p>
          <div className="scenario-grid">
            {(catalog.data?.scenarios ?? []).map((scenario) => {
              const checked = selected.includes(scenario.scenario_id);
              return (
                <label className="scenario-option" key={scenario.scenario_id} data-selected={checked || undefined}>
                  <input type="checkbox" checked={checked} onChange={() => toggle(scenario.scenario_id)} disabled={!checked && selected.length >= maximum} />
                  <span><strong>{scenario.scenario_id}</strong><small>{scenario.point} · {scenario.delay_ms} ms delay · max {scenario.max_injections}</small></span>
                </label>
              );
            })}
          </div>
          <label className="confirmation-row">
            <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
            I confirm this run uses a separate stub runtime and unique database.
          </label>
          <button type="submit" disabled={!confirmed || selected.length === 0 || run.isPending}>
            {run.isPending ? "Running controlled test…" : "Launch controlled test"}
          </button>
        </fieldset>
      </form>

      {run.isError ? <div className="experiment-alert" role="alert">{errorMessage(run.error)}</div> : null}
      {run.data && summary ? (
        <div className="experiment-evidence">
          <p className="experiment-note" role="status">Controlled experiment completed: {summary.expected_outcomes_met} of {summary.scenarios} expected outcomes observed.</p>
          <article className="experiment-result" aria-labelledby="run-summary-title">
            <div className="result-title"><div><p className="eyebrow">Measured isolated run</p><h3 id="run-summary-title">Reliability envelope</h3></div><code>{run.data.report.run_id}</code></div>
            <dl className="experiment-metrics">
              <EvidenceMetric label="Expected outcomes" value={`${summary.expected_outcomes_met}/${summary.scenarios}`} detail={`${formatNumber(summary.expected_outcome_rate_percent)}% matched`} />
              <EvidenceMetric label="Contained" value={`${summary.contained}/${summary.scenarios}`} detail={`${formatNumber(summary.containment_rate_percent)}% containment`} />
              <EvidenceMetric label="Recovery" value={`${summary.recovery_successes}/${summary.recovery_attempts}`} detail={summary.recovery_attempts ? `${formatNumber(summary.recovery_success_rate_percent)}% successful` : "No recovery scenario selected"} />
              <EvidenceMetric label="Added latency P95" value={`${formatNumber(summary.added_latency_ms.p95)} ms`} detail={`${summary.added_latency_ms.count} measured scenario(s)`} />
              <EvidenceMetric label="Database integrity" value={run.data.report.database_integrity} detail="Unique experiment database" />
              <EvidenceMetric label="Real model calls" value={summary.real_llm_calls} detail="Deterministic stub harness" />
            </dl>
          </article>
          <article className="propagation-panel" aria-labelledby="propagation-title">
            <div className="result-title"><div><p className="eyebrow">Expected → actual → boundary</p><h3 id="propagation-title">Failure propagation & recovery</h3></div><span>{run.data.report.scenarios.length} result(s)</span></div>
            <ol className="propagation-list">{run.data.report.scenarios.map((outcome) => <ChaosOutcome key={outcome.scenario_id} outcome={outcome} />)}</ol>
          </article>
        </div>
      ) : null}
    </section>
  );
}

function SecurityOutcome({ outcome }: { outcome: SecurityCaseResult }) {
  const evidence = Object.entries(outcome.evidence).filter(([, value]) => value != null);
  return (
    <tr>
      <th scope="row"><strong>{outcome.case_id}</strong><small>{outcome.category}</small></th>
      <td><StatusToken tone={outcome.status === "PASS" ? "healthy" : "critical"}>{outcome.status === "PASS" ? "Defense held" : "Regression failed"}</StatusToken></td>
      <td><span>{outcome.expected}</span><small>Expected defense</small></td>
      <td><span>{outcome.actual}</span><small>Observed action</small></td>
      <td>{evidence.length ? <ul className="evidence-tags">{evidence.map(([key, value]) => <li key={key}><span>{key.replaceAll("_", " ")}</span> {primitiveEvidence(value)}</li>)}</ul> : "No additional evidence"}</td>
      <td>{formatNumber(outcome.duration_ms, 3)} ms</td>
    </tr>
  );
}

function SecurityWorkspace() {
  const [selected, setSelected] = useState<string[]>([]);
  const [confirmed, setConfirmed] = useState(false);
  const [category, setCategory] = useState("all");
  const catalog = useQuery({ queryKey: ["security-catalog"], queryFn: ({ signal }) => runtimeApi.securityCatalog(signal) });
  const retained = useQuery({ queryKey: ["security-results"], queryFn: ({ signal }) => runtimeApi.securityResults(signal) });
  const run = useMutation({ mutationFn: (cases: string[]) => runtimeApi.runSecurity(cases) });
  const evidence: SecurityResultsData | undefined = run.data ?? retained.data;
  const categories = [...new Set((catalog.data?.cases ?? []).map((item) => item.category))];
  const cases = evidence?.report.cases.filter((item) => category === "all" || item.category === category) ?? [];

  const toggle = (caseId: string) => setSelected((current) => current.includes(caseId)
    ? current.filter((item) => item !== caseId)
    : [...current, caseId]);

  return (
    <section className="experiment-lab" aria-labelledby="experiment-title">
      <header className="experiment-heading">
        <div>
          <p className="eyebrow">Deterministic adversarial regression</p>
          <h2 id="experiment-title">Security lab</h2>
          <p>Execute bounded defensive cases and inspect observed blocked actions. Passing results are regression evidence, not certification.</p>
        </div>
        <StatusToken tone={run.isPending ? "active" : evidence?.report.summary.failed ? "critical" : evidence ? "partial" : "unavailable"}>
          {run.isPending ? "Suite running" : evidence?.report.summary.failed ? `${evidence.report.summary.failed} failed` : evidence ? "Bounded evidence" : "No evidence"}
        </StatusToken>
      </header>

      {catalog.isError ? <div className="experiment-alert" role="alert">{errorMessage(catalog.error)}</div> : null}
      <form className="scenario-console security-console" onSubmit={(event) => { event.preventDefault(); run.mutate(selected); }}>
        <fieldset disabled={catalog.isPending || run.isPending}>
          <legend>Adversarial cases <span>{selected.length}/{catalog.data?.maximum_cases_per_run ?? "—"} selected</span></legend>
          <p className="experiment-boundary">{catalog.data?.scope ?? "Loading security scope…"}</p>
          <div className="selection-actions">
            <button type="button" onClick={() => setSelected((catalog.data?.cases ?? []).map((item) => item.case_id))}>Select all</button>
            <button type="button" onClick={() => setSelected([])}>Clear</button>
          </div>
          <div className="security-case-grid">
            {(catalog.data?.cases ?? []).map((item) => {
              const checked = selected.includes(item.case_id);
              return (
                <label className="scenario-option" key={item.case_id} data-selected={checked || undefined}>
                  <input type="checkbox" checked={checked} onChange={() => toggle(item.case_id)} />
                  <span><strong>{item.case_id}</strong><small>{item.category} · {item.expected}</small></span>
                </label>
              );
            })}
          </div>
          <label className="confirmation-row">
            <input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
            I confirm this suite uses a deterministic stub runtime and writes retained local evidence.
          </label>
          <button type="submit" disabled={!confirmed || selected.length === 0 || run.isPending}>
            {run.isPending ? "Running security suite…" : "Execute security suite"}
          </button>
        </fieldset>
      </form>

      {run.isError ? <div className="experiment-alert" role="alert">{errorMessage(run.error)}</div> : null}
      {retained.isError && !run.data ? <div className="experiment-note">No retained report is currently available. A confirmed run will create one.</div> : null}
      {evidence ? (
        <div className="experiment-evidence">
          <p className="experiment-note" role="status">Security evidence loaded: {evidence.report.summary.passed} of {evidence.report.summary.cases} expected defenses held.</p>
          <article className="experiment-result" aria-labelledby="security-summary-title">
            <div className="result-title"><div><p className="eyebrow">{run.data ? "Newly executed suite" : "Latest retained suite"}</p><h3 id="security-summary-title">Defensive regression envelope</h3></div><code>{evidence.result_id}</code></div>
            <p className="security-disclaimer">{evidence.report.disclaimer} {evidence.scope}</p>
            <dl className="experiment-metrics">
              <EvidenceMetric label="Defenses held" value={`${evidence.report.summary.passed}/${evidence.report.summary.cases}`} detail={`${formatNumber(evidence.report.summary.pass_rate_percent)}% expected outcomes`} />
              <EvidenceMetric label="Regressions" value={evidence.report.summary.failed} detail="Unexpected defensive outcomes" />
              <EvidenceMetric label="Integrity" value={evidence.report.summary.integrity_check} detail="Experiment database check" />
              <EvidenceMetric label="Duration" value={`${formatNumber(evidence.report.summary.total_duration_ms, 3)} ms`} detail={evidence.report.generated_at_utc} />
              <EvidenceMetric label="Real model calls" value={evidence.report.summary.real_llm_calls} detail="Deterministic adversarial harness" />
              <EvidenceMetric label="Maturity" value="Partial" detail="Not a penetration test or certification" />
            </dl>
          </article>
          <article className="security-results" aria-labelledby="security-results-title">
            <div className="result-title">
              <div><p className="eyebrow">Attack → policy → observed action</p><h3 id="security-results-title">Attack results & blocked actions</h3></div>
              <label>Category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">All categories</option>{categories.map((item) => <option value={item} key={item}>{item}</option>)}</select></label>
            </div>
            <div className="security-table-wrap">
              <table>
                <thead><tr><th>Case</th><th>Result</th><th>Attack expectation</th><th>Observed action</th><th>Evidence</th><th>Duration</th></tr></thead>
                <tbody>{cases.map((outcome) => <SecurityOutcome key={outcome.case_id} outcome={outcome} />)}</tbody>
              </table>
            </div>
            {cases.length === 0 ? <p className="experiment-note">No results match this category.</p> : null}
          </article>
        </div>
      ) : null}
    </section>
  );
}

function ChaosSecurityLab({ focus }: ChaosSecurityLabProps) {
  return focus === "chaos" ? <ChaosWorkspace /> : <SecurityWorkspace />;
}

export { ChaosSecurityLab };
