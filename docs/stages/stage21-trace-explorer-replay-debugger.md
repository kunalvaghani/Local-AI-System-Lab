# Stage 21 — Trace Explorer & Replay Debugger

## Stage Completed

Stage 21 turns the existing safe trace and replay API into a professional local
debugging workbench. It is for explaining exactly how one selected execution
progressed, which boundaries were deterministic, and what a bounded replay
verified. It stops before Stage 22 Hardware & Performance Lab UI.

## Expected Output

- An ordered execution timeline with expandable trace steps.
- Search and filters for model calls, tool calls, state transitions, failures,
  determinism classes, and components.
- Honest timing visualization, redaction, integrity, and replay boundaries.
- Explicit deterministic replay controls and per-step outcomes.
- A stable deep link to the selected task and expanded step.
- A bounded interface that remains usable with a 10,000-step fixture.

## Actual Output

| Component | What it does | Stage 21 upgrade |
| --- | --- | --- |
| Trace query owner | Retrieves the selected task's safe trace and polls only while that task is active | Replaces the trace endpoint placeholder with real loopback evidence |
| Execution timeline | Orders every reported step and classifies runtime, model, tool, state, and failure evidence | Makes a previous run visually debuggable step by step |
| Step expansion | Shows timestamp, actor, component, state, model, semantic/input/output hashes, chain link, and safe failure | Converts summary nodes into inspectable evidence without exposing redacted payloads |
| URL step selector | Validates and preserves `?task=` plus optional `?step=` through native history | Makes expanded evidence refreshable and shareable locally |
| Search and filters | Searches evidence and filters by kind, determinism, and component | Lets operators isolate relevant boundaries without changing server truth |
| Timestamp-gap bars | Scales the exact interval from the prior recorded step and labels it `Δ` | Adds timing shape while avoiding a false per-component latency claim |
| Bounded paging | Renders 100 filtered rows per page; deferred search and memoized maps bound repeat work | Verifies a 10,000-step trace without a 10,000-node DOM |
| Replay control | Explicitly posts to the existing replay endpoint | Keeps replay a deliberate diagnostic action rather than an automatic side effect |
| Replay outcome panel | Shows integrity, reconstructed state, counts, and each outcome/reason | Explains matched, diverged, observed, skipped-side-effect, and integrity-failure results |
| Comparison boundary | Reports that cross-run comparison is unavailable | Avoids fabricating divergence evidence the API does not expose |

## New Demonstrable Capability

An operator can launch or select a completed local task, open its trace, filter
or search the ordered execution, deep-link to a hash-chained step, understand
state/model/tool boundaries, and explicitly verify deterministic replay. The
real Stage 21 smoke demonstrated a completed 16-step trace and valid replay with
11 matched deterministic steps and five observed nondeterministic/observational
steps. That real inference task emitted zero tool steps, and the UI reports zero
rather than inventing tool activity.

## Files Added

- `apps/web/src/components/trace/TraceExplorer.tsx`
- `apps/web/src/hooks/useSelectedTraceStep.ts`
- `apps/web/src/styles/traces.css`
- `apps/web/scripts/stage21-smoke.mjs`
- `benchmarks/results/stage21-trace-replay-20260825T130714Z.json`
- `docs/adr/0021-redacted-trace-projection-and-explicit-replay.md`
- `docs/stages/stage21-trace-explorer-replay-debugger.md`

## Files Modified

- Frontend typed API, query ownership, route composition, identity, styles,
  fixtures, and component tests under `apps/web/`.
- `README.md`, `PROJECT_STATE.md`, and development, architecture, repository,
  ADR-index, and risk documentation under `docs/`.

## Tests Performed

- 18 frontend component tests, including four route-specific automated axe scans.
- 10,000-step fixture with exactly 100 rendered timeline rows on each tested page.
- Real Vite proxy/API trace retrieval and replay smoke.
- 150 backend regression tests and Python compile validation.
- Production TypeScript/Vite build, gzip bundle gate, and diff hygiene checks.

## Measurements

- Real trace: 16 steps over 692 ms; 11 deterministic, three nondeterministic,
  two observational, zero side-effecting, five state transitions, two model
  steps, and zero tool steps.
- Trace retrieval: 19.362 ms.
- Replay: `matched`, integrity valid, reconstructed state `completed`, 11
  matched, zero diverged, five observed, zero skipped, zero integrity failures;
  29.216 ms.
- Complete real smoke: 841.405 ms.
- 10,000-step/100-row focused interaction: 2.284 seconds in the final suite.
- Frontend tests: 18/18, 6.94 seconds test time; backend tests: 150/150,
  36.857 seconds.
- Production build: 215 modules; 124,662 gzip JavaScript bytes (48.7% of the
  256,000-byte gate) and 6,393 gzip CSS bytes.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| Step debugging | Expand an ordered prior run | Delivered with URL-addressable details and hashes |
| Model/tool/state visibility | Filter real classified calls and transitions | Delivered; real smoke truthfully had two model and zero tool steps |
| Timing | Show latency/timing shape without false precision | Delivered as exact recorded timestamp gaps, explicitly not step duration |
| Replay | Control and explain bounded replay | Delivered as explicit mutation with aggregate and per-step outcomes |
| Divergence | Compare what the backend can prove | Same-run replay divergence delivered; cross-run comparison labelled unavailable |
| Scale | Avoid an unbounded rendered trace | Delivered and tested at 10,000 fetched steps / 100 rendered rows |
| Security | Preserve API redaction | Delivered; smoke verifies raw payloads are absent |

## Problems / Technical Debt

- The API returns the full selected trace; server-side pagination or streaming
  may be needed for traces beyond the validated local scale.
- No cross-run safe comparison endpoint exists, so divergence comparison is
  limited to replay outcomes for one source run.
- Recorded timestamp gaps are not isolated component execution durations.
- Manual computed-contrast, forced-color, zoom/reflow, and screen-reader checks
  remain outside automated jsdom coverage.
- The existing Windows development server can log a harmless disconnected-
  client traceback when active browser polling is stopped.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` records Stage 21 complete, its safe trace/replay decisions,
validation evidence, measurements, known limits, and the Stage 22 approval gate.

## Next Stage

Stage 22 — Hardware & Performance Lab UI. No Stage 22 implementation was
started.
