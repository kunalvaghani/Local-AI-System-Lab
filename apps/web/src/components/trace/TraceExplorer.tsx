import { useDeferredValue, useMemo, useState } from "react";

import type { DeterminismClass, ReplayOutcome, TraceStep } from "../../api/types";
import { useSelectedTaskId } from "../../hooks/useSelectedTaskId";
import { useSelectedTraceStep } from "../../hooks/useSelectedTraceStep";
import { useReplayTraceMutation, useTaskQuery, useTaskTraceQuery } from "../../query/runtimeQueries";
import { StatusToken, type StatusTone } from "../StatusToken";

const PAGE_SIZE = 100;
const EMPTY_STEPS: TraceStep[] = [];
const terminalStatuses = new Set(["completed", "failed", "cancelled", "timed_out"]);
const determinismTone: Record<DeterminismClass, StatusTone> = {
  deterministic: "healthy", nondeterministic: "unknown", side_effecting: "warning", observational: "partial",
};
const replayTone: Record<ReplayOutcome, StatusTone> = {
  matched: "healthy", diverged: "critical", observed_only: "unknown", skipped_side_effect: "warning", integrity_failed: "critical",
};

function timestamp(value: string) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Invalid timestamp" : parsed.toLocaleTimeString();
}

function duration(start: string, finish: string | null) {
  if (!finish) return null;
  const milliseconds = new Date(finish).getTime() - new Date(start).getTime();
  return Number.isFinite(milliseconds) && milliseconds >= 0 ? milliseconds : null;
}

function formatMs(value: number | null) {
  return value === null ? "Unavailable" : `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 }).format(value)} ms`;
}

function stepKind(step: TraceStep) {
  if (step.event_name.startsWith("model.")) return "model";
  if (step.event_name.startsWith("tool.")) return "tool";
  if (step.event_name === "task.state.changed") return "state";
  if (step.failure) return "failure";
  return "runtime";
}

function matchesKind(step: TraceStep, kind: string) {
  if (kind === "all") return true;
  if (kind === "failure") return step.failure !== null;
  return stepKind(step) === kind;
}

function gapFromPrior(steps: TraceStep[], index: number) {
  if (index === 0) return 0;
  const value = new Date(steps[index].recorded_at_utc).getTime() - new Date(steps[index - 1].recorded_at_utc).getTime();
  return Number.isFinite(value) && value >= 0 ? value : 0;
}

function TraceStepDetail({ step, replayOutcome }: { step: TraceStep; replayOutcome: { outcome: ReplayOutcome; reason: string } | null }) {
  return (
    <div className="trace-step-detail">
      <dl>
        <div><dt>Step ID</dt><dd><code>{step.step_id}</code></dd></div>
        <div><dt>Recorded</dt><dd><time dateTime={step.recorded_at_utc}>{step.recorded_at_utc}</time></dd></div>
        <div><dt>Actor</dt><dd>{step.actor}</dd></div>
        <div><dt>Component</dt><dd>{step.component}</dd></div>
        <div><dt>State</dt><dd>{step.state_to ? `${step.state_from ?? "∅"} → ${step.state_to}` : "No transition"}</dd></div>
        <div><dt>Model</dt><dd>{step.model_id ?? "Unavailable"}</dd></div>
        <div><dt>Input hash</dt><dd><code>{step.input_hash}</code></dd></div>
        <div><dt>Output hash</dt><dd><code>{step.output_hash}</code></dd></div>
        <div><dt>Semantic hash</dt><dd><code>{step.semantic_hash}</code></dd></div>
        <div><dt>Chain link</dt><dd><code>{step.previous_hash} → {step.step_hash}</code></dd></div>
      </dl>
      {step.failure ? <p className="trace-failure" role="status">Failure: {step.failure.code}. Details are omitted by the API boundary.</p> : null}
      {replayOutcome ? <div className="trace-replay-outcome"><StatusToken tone={replayTone[replayOutcome.outcome]}>{replayOutcome.outcome}</StatusToken><p>{replayOutcome.reason}</p></div> : null}
      <p className="trace-redaction-note">Input and output payloads are not returned to the browser; only integrity hashes are inspectable.</p>
    </div>
  );
}

function TraceExplorer() {
  const { taskId } = useSelectedTaskId();
  const { stepId, selectStep } = useSelectedTraceStep();
  const task = useTaskQuery(taskId);
  const live = task.data ? !terminalStatuses.has(task.data.status) : true;
  const trace = useTaskTraceQuery(taskId, live);
  const replay = useReplayTraceMutation();
  const [search, setSearch] = useState("");
  const [determinism, setDeterminism] = useState<DeterminismClass | "all">("all");
  const [component, setComponent] = useState("all");
  const [kind, setKind] = useState("all");
  const [page, setPage] = useState(0);

  const allSteps = trace.data?.steps ?? EMPTY_STEPS;
  const replayData = replay.data?.source_run_id === trace.data?.run.run_id ? replay.data : undefined;
  const components = useMemo(() => [...new Set(allSteps.map((step) => step.component))].sort(), [allSteps]);
  const normalizedSearch = useDeferredValue(search.trim().toLocaleLowerCase());
  const filtered = useMemo(() => allSteps.filter((step) => {
    const matchesSearch = !normalizedSearch || [step.event_name, step.actor, step.component, step.step_id, step.state_from, step.state_to, step.model_id, step.failure?.code]
      .some((value) => value?.toLocaleLowerCase().includes(normalizedSearch));
    return matchesSearch && (determinism === "all" || step.determinism === determinism) && (component === "all" || step.component === component) && matchesKind(step, kind);
  }), [allSteps, component, determinism, kind, normalizedSearch]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);
  const gaps = useMemo(() => allSteps.map((_, index) => gapFromPrior(allSteps, index)), [allSteps]);
  const maxGap = Math.max(1, ...gaps);
  const stepIndexById = useMemo(() => new Map(allSteps.map((step, index) => [step.step_id, index])), [allSteps]);
  const replayByStep = useMemo(() => new Map(replayData?.steps.map((step) => [step.step_id, step]) ?? []), [replayData]);
  const totalDuration = trace.data ? duration(trace.data.run.started_at_utc, trace.data.run.finished_at_utc) : null;
  const resetPage = () => setPage(0);

  return (
    <section className="trace-explorer" aria-labelledby="trace-explorer-title">
      <div className="trace-section-heading">
        <div><p className="eyebrow">Hash-chained execution evidence</p><h2 id="trace-explorer-title">Trace explorer</h2><p>Debug one previous run step-by-step without replaying model generation or tool side effects.</p></div>
        {trace.isPending && taskId ? <StatusToken tone="queued">Loading trace</StatusToken> : trace.isError ? <StatusToken tone="critical">Trace unavailable</StatusToken> : trace.data ? <StatusToken tone={trace.data.run.status === "completed" ? "healthy" : "warning"}>{trace.data.run.status}</StatusToken> : <StatusToken tone="unavailable">No selection</StatusToken>}
      </div>

      {taskId === null ? <article className="task-context-empty"><h3>Select a runtime task to inspect its trace.</h3><p>Launch a task or open this route with a valid <code>?task=</code> selection. No run is inferred from browser history.</p></article>
        : trace.isPending ? <p className="panel-empty">Loading redacted trace evidence…</p>
          : trace.isError || !trace.data ? <div className="runtime-error" role="alert"><strong>Trace evidence unavailable.</strong><p>{trace.error?.message}</p></div>
            : <>
              <div className="trace-run-strip">
                <div><span>Run</span><code>{trace.data.run.run_id}</code></div><div><span>Task</span><code>{trace.data.run.task_id}</code></div><div><span>Model</span><strong>{trace.data.run.model_id ?? "Unavailable"}</strong></div><div><span>Duration</span><strong>{formatMs(totalDuration)}</strong></div><div><span>Steps</span><strong>{allSteps.length}</strong></div><div><span>Chain</span><code>{trace.data.run.final_chain_hash ?? "Unavailable"}</code></div>
              </div>

              <div className="trace-workbench">
                <article className="trace-timeline-panel">
                  <div className="panel-title-row"><div><p className="eyebrow">Recorded order</p><h3>Execution timeline</h3></div><span>{filtered.length} / {allSteps.length}</span></div>
                  <form className="trace-filter-bar" onSubmit={(event) => event.preventDefault()}>
                    <label><span>Search trace</span><input type="search" value={search} onChange={(event) => { setSearch(event.target.value); resetPage(); }} placeholder="Event, actor, state, hash…" /></label>
                    <label><span>Kind</span><select value={kind} onChange={(event) => { setKind(event.target.value); resetPage(); }}><option value="all">All kinds</option><option value="model">Model calls</option><option value="tool">Tool calls</option><option value="state">State transitions</option><option value="failure">Failures</option><option value="runtime">Runtime</option></select></label>
                    <label><span>Determinism</span><select value={determinism} onChange={(event) => { setDeterminism(event.target.value as DeterminismClass | "all"); resetPage(); }}><option value="all">All classes</option><option value="deterministic">Deterministic</option><option value="nondeterministic">Nondeterministic</option><option value="side_effecting">Side-effecting</option><option value="observational">Observational</option></select></label>
                    <label><span>Component</span><select value={component} onChange={(event) => { setComponent(event.target.value); resetPage(); }}><option value="all">All components</option>{components.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
                  </form>

                  {visible.length === 0 ? <p className="panel-empty">No trace steps match the current filters.</p> : <ol className="trace-timeline">
                    {visible.map((step) => {
                      const originalIndex = stepIndexById.get(step.step_id) ?? 0;
                      const gap = gaps[originalIndex] ?? 0;
                      const expanded = step.step_id === stepId;
                      const replayStep = replayByStep.get(step.step_id) ?? null;
                      return <li data-expanded={expanded ? "true" : "false"} key={step.step_id}>
                        <button aria-expanded={expanded} className="trace-step-button" onClick={() => selectStep(expanded ? null : step.step_id)} type="button">
                          <span className="trace-ordinal">{String(step.ordinal).padStart(2, "0")}</span><span className="trace-node" aria-hidden="true" /><span className="trace-step-summary"><strong>{step.event_name}</strong><small><span data-kind={stepKind(step)}>{stepKind(step)}</span> · {step.actor} · {step.component}{step.state_to ? ` · ${step.state_from ?? "∅"} → ${step.state_to}` : ""}</small></span><StatusToken tone={determinismTone[step.determinism]}>{step.determinism}</StatusToken><span className="trace-gap"><i style={{ "--gap-width": `${Math.max(2, gap / maxGap * 100)}%` } as React.CSSProperties} /><small>Δ {formatMs(gap)}</small></span><time dateTime={step.recorded_at_utc}>{timestamp(step.recorded_at_utc)}</time>
                        </button>
                        {expanded ? <TraceStepDetail replayOutcome={replayStep} step={step} /> : null}
                      </li>;
                    })}
                  </ol>}
                  {pageCount > 1 ? <nav className="trace-pagination" aria-label="Trace pages"><button type="button" disabled={safePage === 0} onClick={() => setPage((value) => Math.max(0, value - 1))}>Previous</button><span>Page {safePage + 1} of {pageCount}</span><button type="button" disabled={safePage >= pageCount - 1} onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}>Next</button></nav> : null}
                  <p className="trace-policy-note">Showing at most {PAGE_SIZE} steps per page. {trace.data.payload_policy}</p>
                </article>

                <aside className="replay-debugger" aria-labelledby="replay-debugger-title">
                  <div className="panel-title-row"><div><p className="eyebrow">Side-effect-free verification</p><h3 id="replay-debugger-title">Replay debugger</h3></div>{replayData ? <StatusToken tone={replayData.integrity_valid ? "healthy" : "critical"}>{replayData.status}</StatusToken> : null}</div>
                  <p>Verify the hash chain and deterministic state reducer. Model generation is observed, and tool side effects are skipped.</p>
                  <button className="replay-button" disabled={replay.isPending} onClick={() => replay.mutate(trace.data.run.run_id)} type="button">{replay.isPending ? "Replaying reducers…" : replayData ? "Run replay again" : "Replay deterministic reducers"}</button>
                  {replay.error ? <p className="form-error" role="alert">{replay.error.message}</p> : null}
                  {replayData ? <>
                    <dl className="replay-summary"><div><dt>Integrity</dt><dd>{replayData.integrity_valid ? "Valid" : "Failed"}</dd></div><div><dt>Reconstructed state</dt><dd>{replayData.reconstructed_state ?? "Unavailable"}</dd></div><div><dt>Matched</dt><dd>{replayData.counts.matched}</dd></div><div><dt>Observed only</dt><dd>{replayData.counts.observed_only}</dd></div><div><dt>Side effects skipped</dt><dd>{replayData.counts.skipped_side_effect}</dd></div><div><dt>Integrity failures</dt><dd>{replayData.counts.integrity_failed}</dd></div></dl>
                    <p className="trace-policy-note">Replay ID <code>{replayData.replay_id}</code>. Expand a timeline step to inspect its replay outcome and reason.</p>
                  </> : <p className="panel-empty">Replay has not been requested. Viewing a trace never starts replay automatically.</p>}
                  <div className="comparison-boundary"><strong>Cross-run divergence</strong><p>The accepted loopback API does not expose trace comparison. This debugger reports replay integrity divergence only and does not fabricate a second run.</p></div>
                </aside>
              </div>
            </>}
    </section>
  );
}

export { TraceExplorer };
