# Stage 20 — Agent & Scheduler Visualization

## Stage Completed

Stage 20 turns the existing `/agents` and `/scheduler` route contracts into
real, task-aware operational views. It stops before Stage 21 Trace Explorer &
Replay Debugger.

## Expected Output

Visually see how selected work moves through the runtime: agent ownership,
durable/live state, resource admission, scheduler placement, queue order,
timings, outcome, and cancellation.

## Actual Output

| Component | What it does | Stage 20 upgrade |
| --- | --- | --- |
| Task-aware navigation | Preserves a validated `?task=` across native route links | Runtime, Agents, and Scheduler share one selected execution |
| Agent catalog | Shows real roles, objectives, capabilities, tools, and permissions | Selected owner is visibly distinguished without simulated activity |
| State path | Projects durable terminal history or bounded live SSE states | Refreshable state-machine evidence replaces log correlation |
| Execution flow | Correlates intake, agent, admission, scheduler, and outcome | Makes cross-component handoffs readable as ordered text |
| Admission panel | Shows real action, reason, confidence, estimate, and constraints | Missing stub admission remains explicitly not reported |
| Scheduler map | Shows real worker occupancy and policy-derived projected queue | Priority/FIFO order is explained without claiming preemption |
| Selected request | Uses live snapshot or retained task scheduler metadata | Completed dispatch remains inspectable after live eviction |
| Request ledger | Shows at most 50 reported requests and timings | Adds bounded table equivalence; does not fabricate task history |
| Cancellation control | Reuses the Stage 19 DELETE mutation | Control is available in both specialist task views |

## New Demonstrable Capability

A user can launch or deep-link one local task, navigate between Runtime, Agents,
and Scheduler without losing context, follow its state and component handoffs,
inspect real queue/admission/timing evidence, and request cancellation.

## Files Added

- `apps/web/src/components/scheduler/AgentVisualization.tsx`
- `apps/web/src/components/scheduler/SelectedExecution.tsx`
- `apps/web/src/components/scheduler/evidence.ts`
- `apps/web/src/styles/agents.css`
- `apps/web/scripts/stage20-smoke.mjs`
- `docs/adr/0020-task-scoped-agent-scheduler-projections.md`
- this report
- retained Stage 20 smoke JSON under `benchmarks/results/`

## Files Modified

Frontend route/query types, navigation, scheduler visualization/styles,
fixtures/tests, version identity, and project documentation/state.

## Tests Performed

- 12 Vitest component tests, including axe scans for Runtime, Agents, and Scheduler
- TypeScript plus Vite production build
- compressed initial-JavaScript budget check
- real Vite proxy/API/SSE Stage 20 smoke
- complete 150-test Python backend regression suite
- Python compile check

## Measurements

- Live stub smoke: 15 lifecycle events, five durable transitions, one terminal
  task event, one end event, 0 ms queue wait, 50.385 ms scheduler execution,
  and 770.484 ms complete smoke.
- Stub admission: `null` by contract and displayed as not reported.
- Final build: 121,569 gzip JavaScript bytes (3,613 bytes / 3.1% above Stage
  19), 5.54 KiB gzip CSS, and 212 transformed modules; the 256,000-byte budget
  passed.
- Frontend: 12 tests passed in 5.43 seconds. Backend: all 150 regression tests
  passed in 40.317 seconds. These are local one-run integration/build samples,
  not throughput claims.

## Expected vs Actual

Expected visible agent states, work progression, scheduler queue/priority,
admission, and control. Actual behavior meets that scope for one selected task.
The live API does not expose global task history, and the deterministic stub
does not emit admission decisions; both limitations remain visibly honest.

## Problems / Technical Debt

- The scheduler inspection endpoint may omit completed request rows; selected
  terminal tasks use their retained authoritative metadata instead.
- There is no list/pagination endpoint for a global task explorer.
- Automated axe results exclude computed color contrast and are not a WCAG
  certification; real-browser keyboard, zoom, forced-color, and screen-reader
  checks remain Stage 25 work.
- High-volume graph virtualization remains Stage 21 performance scope.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` now records Stage 20 complete, measurements, limitations,
decisions, and the Stage 21 approval gate.

## Next Stage

Stage 21 — Trace Explorer & Replay Debugger. No Stage 21 implementation is
included here.
