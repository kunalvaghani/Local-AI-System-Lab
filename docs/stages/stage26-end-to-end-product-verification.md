# Stage 26 — End-to-End Product Verification

## Stage Completed

Stage 26 verifies the assembled local product as one release-candidate story. It
is for proving that a user action can cross the React workbench, loopback proxy,
HTTP API, runtime, scheduler, router, local model, safe-tool policy, SQLite,
telemetry, trace/replay, and visible recovery boundaries. It stops before Stage
27 and does not claim remote, multi-user, or production-server readiness.

## What This Stage Is For

- Exercise one reproducible browser journey through every implemented specialist
  route instead of accepting isolated component demonstrations.
- Verify both inference and exact-grant read-only tool execution through real API
  boundaries, persistence, telemetry, and redacted trace/replay.
- Prove visible fail-closed behavior for malformed input, denied authority,
  unconfirmed chaos, terminal cancellation, missing tasks, and a disconnected API.
- Restart the API against the same SQLite database and verify the completed task
  remains inspectable through the built frontend.
- Combine the existing real-model backend gate, complete frontend regressions,
  production build, bundle ceiling, accessibility audit, and browser evidence into
  one retained release-candidate decision.

## Component Upgrades

| Component | What it does | Stage 26 upgrade |
| --- | --- | --- |
| Tool application service | Catalogues and runs registered runtime tools | Adds `GET /v1/tools` and `POST /v1/tools/execute` with exact fields, exact agent grants, bounded synchronous execution, and typed fail-closed responses |
| Safe Tool Probe | Lets an operator exercise one approved read-only tool | Renders server-owned agents/tools/permissions, requires an explicit catalogued selection, shows durable task/trace identity, duration, state, and bounded content |
| Durable task inspection | Restores completed task evidence after process restart | Normalizes persisted inference output to the same result shape used by live API records and reconstructs state history for frontend rendering |
| Vite proxy/preview | Serves the local React workbench over the loopback API | Accepts validated loopback target and port overrides so acceptance can run on isolated random ports without touching an existing development stack |
| Browser journey | Operates the product like a user | Launches a task, verifies eight real routes, replays inference and tool traces, injects an API outage, checks recovery, audits WCAG A/AA rules, captures vitals, and repeats after restart |
| Product acceptance runner | Owns the release-candidate decision | Runs the Stage 16 real-model gate, frontend tests/build/bundle gate, isolated API/preview/Chromium stack, success/failure/restart checks, cleanup, and retained JSON evidence |
| Acceptance policy | Defines the pass/fail contract before execution | Requires 151+ backend tests, 39+ frontend tests, eight routes, five exact failure statuses, 120 s browser ceiling, 1 s tool ceiling, and 256,000-byte gzip JS ceiling |

## Expected Output

- A reproducible release-candidate command that owns isolated processes and data.
- A real browser flow through frontend, API, runtime, scheduler/router/model,
  tools, persistence, telemetry, trace/replay, and visualization.
- Explicit success, failure, API-disconnect/reconnect, and API-restart evidence.
- Retained machine-readable measurements with required-category classifications.

## Actual Output

- `python -m benchmarks.run_stage26_product_acceptance` completed successfully and
  retained `stage26-product-acceptance-20260827T101438Z.json`.
- All seven Stage 26 required categories passed and the result is a release
  candidate for the single-user loopback portfolio scope.
- Overall maturity remains `PARTIAL`: restart/recovery retains the known narrow
  terminal-output atomicity gap; security/chaos remain bounded evidence rather
  than certification; remote multi-user deployment is deferred.
- An earlier Python 3.11 diagnostic reproduced a Windows SQLite temporary-file
  cleanup incompatibility in the injected database-failure test. The established
  Python 3.10 project runtime passed the complete gate; the 3.11 incompatibility
  is tracked rather than hidden.

## New Demonstrable Capability

From `/runtime`, an operator can launch a bounded local inference task, watch it
complete, retain its identity across Agent, Scheduler, Hardware, Metrics, and
Trace views, replay deterministic reducers, execute a server-catalogued
path-restricted project read, inspect its persisted tool trace without repeating
the side effect, observe a visible API outage/recovery, and reload the completed
task after the API process restarts against the same database.

## Files Added

- `apps/web/scripts/stage26-browser.mjs`
- `apps/web/src/components/runtime/ToolProbe.tsx`
- `benchmarks/run_stage26_product_acceptance.py`
- `benchmarks/results/stage26-product-acceptance-20260827T101438Z.json`
- `configs/product-acceptance.json`
- `docs/adr/0026-isolated-full-story-product-acceptance.md`
- `docs/stages/stage26-end-to-end-product-verification.md`
- `tests/test_product_acceptance.py`

## Files Modified

- Runtime API server/service/OpenAPI/task-manager and API tests.
- Frontend API types/client/query ownership, Runtime Command Center, Tool Probe
  styles/fixtures/tests, Vite environment handling, package scripts/dependencies,
  TypeScript configuration, Stage identity, and lockfile.
- README, project state, architecture, development, repository map, ADR index,
  and risk register.

## Tests Performed

- Stage 16 backend acceptance: 14/14 required categories passed, including 154
  Python tests and one real llama.cpp/Qwen API inference.
- Frontend: 39/39 Vitest/Testing Library/axe tests passed.
- Focused Stage 26 backend/API policy tests: 5/5 passed.
- Production TypeScript/Vite build passed; compressed JavaScript gate passed.
- Browser: eight real routes, inference and tool traces/replay, disconnected and
  recovered API states, five exact failure responses, zero page/console errors,
  zero axe WCAG A/AA violations, and post-restart task recovery passed.

## Measurements

- Complete backend acceptance: 91,410.474 ms.
- Frontend tests: 35,391.660 ms; build: 5,929.256 ms; bundle gate: 1,565.495 ms.
- Browser product journey: 65,656.979 ms across eight routes.
- Built JavaScript: 150,997 gzip bytes, 59.0% of the 256,000-byte ceiling.
- Real inference: 1,801.341 ms TTFT, 103.47 tokens/s, 2,408.659 ms total,
  1,343.680 MiB peak process RAM, and 1,189 MiB VRAM delta.
- Tool execution: 2.531 ms; inference and tool traces each contained 16 steps.
- Browser vitals on the isolated local preview: 2.5 ms TTFB, 76 ms FCP/LCP,
  CLS 0.01. INP was unavailable because the harness did not collect a qualifying
  interaction; these are one-run lab measurements, not field Core Web Vitals.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| Complete success flow | Every implemented product boundary exercised | PASS: browser → proxy → API → runtime → scheduler/router/model → persistence/telemetry/trace → UI |
| Safe tool flow | Server-catalogued exact-grant execution | PASS: project read completed in 2.531 ms with durable 16-step trace and skipped side effects during replay |
| Failure behavior | Known failures remain visible and fail closed | PASS: invalid 400, denied tool 403, unconfirmed chaos 400, terminal cancel 409, missing task 404, plus visible API outage/recovery |
| Restart durability | Completed evidence survives API restart | PASS: SQLite integrity `ok`; inference/tool output types retained; browser recovered the completed task |
| Backend regression | Existing release candidate remains green | PASS: 154 tests, all 14 categories, one real LLM call, benchmark thresholds met |
| Frontend regression | Tests/build/bundle remain green | PASS: 39 tests, production build, 150,997/256,000 gzip bytes |
| Browser quality | Real routes render without known automation violations | PASS: eight routes, zero overlay/page/console errors, zero axe A/AA violations |
| Product maturity | Honest scoped classification | `release_candidate=true`; overall `PARTIAL`; remote multi-user deployment `DEFERRED` |

## Problems / Technical Debt

- The standard-library HTTP adapter and Vite preview remain local development
  infrastructure, not a hardened production serving stack.
- Active task ownership/SSE cursors are process-local; only completed durable
  evidence and the existing safe recovery checkpoint are promised across restart.
- Persisted tool task results still use the explicit durable output envelope;
  persisted inference results are normalized for the current workbench contract.
- The known terminal-state/output atomicity gap remains and keeps recovery partial.
- Accessibility automation is not a human screen-reader or conformance review.
- The single JavaScript chunk still exceeds Vite's 500 kB uncompressed warning,
  although the tracked gzip ceiling passes.
- Python 3.11 on Windows can retain the deliberately faulted SQLite handle through
  temporary-directory cleanup; Python 3.10 is the verified project runtime.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` now identifies Stage 26 as complete, records the release
candidate evidence and new tool/restart contracts, preserves all known scope
limitations, and sets Stage 27 as the next approval-gated stage.

## Next Stage

Stage 27 — Product Demonstration & Portfolio Packaging. No Stage 27
implementation was started.
