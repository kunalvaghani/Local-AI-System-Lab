# ADR-0026 — Isolated full-story product acceptance

- Status: Accepted
- Date: 2026-08-27
- Stage: 26

## Context

Stages 16–25 verified backend and frontend subsystems independently, but no
single retained gate proved the complete user story across the built client,
proxy, API, runtime, scheduler/router/model, safe tools, persistence, telemetry,
trace/replay, visible failure states, and restart recovery. The safe tool runtime
also lacked a bounded external surface, leaving one required product boundary
unreachable from the workbench.

An acceptance run must not reuse or terminate an unknown development service,
must not leak test data into the normal database, and must not replace the real
model gate with a stub-only browser demonstration.

## Decision

Add a read-only server-owned tool catalog and bounded synchronous execution
endpoint. Keep exact runtime agent grants, typed argument validation, path
containment, timeout policy, persistence, trace, and telemetry authoritative;
the browser never invents tools or permissions.

Run product acceptance on random loopback API/preview ports with a unique
temporary SQLite database and a uniquely named project-pinned Chromium session.
The runner owns and cleans up only the processes it starts. Combine the existing
Stage 16 real-model acceptance with frontend tests/build/bundle checks, then run
one deterministic stub browser journey for repeatable interface, failure,
tool-side-effect, and restart evidence.

Normalize restored inference outputs to the live task-result API shape so a URL-
selected task renders identically before and after API restart. Preserve the
explicit durable envelope for tool-only tasks until a broader discriminated task
result contract is approved.

Classify binary required categories separately from subsystem maturity. A
release candidate may remain overall `PARTIAL` and may be accepted only for the
measured single-user loopback portfolio scope.

## Consequences

- One command now retains evidence for real inference, all regressions, the built
  client, eight routes, safe tools, five exact failure statuses, API outage and
  reconnect, accessibility automation, and durable restart rendering.
- Browser verification is reproducible without interfering with an already-open
  local development instance.
- Agent Browser becomes one exact development-only dependency; it does not enter
  the production bundle.
- Stub browser inference proves deterministic integration while the separate
  Stage 16 sub-gate proves one real local model call and performance thresholds.
- Remote/multi-user serving, certification, active-task continuation, the narrow
  atomicity gap, and a unified inference/tool result union remain outside scope.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Verify only component tests and API scripts | Rejected | It does not prove browser routing, proxying, user interaction, visible failures, or restart rendering |
| Drive the existing ports/database | Rejected | It can contaminate user state or interfere with unrelated services |
| Use only the deterministic stub | Rejected | It cannot substantiate the measured real-model release claim |
| Use the real model for every browser retry | Rejected | It makes UI failure diagnosis slow and nondeterministic; the inherited real-model gate already verifies that boundary |
| Hard-code tools in the frontend | Rejected | Browser/server authority would drift and the client could imply grants it does not own |
| Expose shell, network, or write tools | Rejected | Stage 26 requires a safe demonstrable boundary, not expanded authority |
| Treat every persisted output envelope as a live inference result | Rejected | Tool and inference records have different semantics; only the required inference recovery shape is normalized |

## Evidence

- `configs/product-acceptance.json`
- `benchmarks/run_stage26_product_acceptance.py`
- `apps/web/scripts/stage26-browser.mjs`
- `benchmarks/results/stage26-product-acceptance-20260827T101438Z.json`
- `tests/test_api.py`
- `tests/test_product_acceptance.py`
- `apps/web/src/App.test.tsx`
- `docs/stages/stage26-end-to-end-product-verification.md`
