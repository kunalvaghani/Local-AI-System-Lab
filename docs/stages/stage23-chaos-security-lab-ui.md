# Stage 23 — Chaos & Security Lab UI

## Stage Completed

Stage 23 turns existing reliability and adversarial backend evidence into two
interactive local workbench routes. It is for demonstrating controlled failures,
propagation, containment, recovery, defensive outcomes, and blocked actions
without relying on terminal output. It stops before Stage 24 interaction/motion polish.

## Expected Output

- Select fault scenarios and launch confirmed controlled tests.
- View failure propagation, containment, recovery behavior, and recovery metrics.
- Execute bounded security cases and inspect attack results and blocked actions.
- Preserve explicit isolation, retention, integrity, and non-certification boundaries.

## Actual Output

| Component | What it does | Stage 23 upgrade |
| --- | --- | --- |
| Chaos catalog | Reports nine configured scenarios and the three-scenario maximum | Removes duplicated browser scenario knowledge |
| Chaos controller | Requires explicit isolation confirmation before synchronous POST | Makes controlled launches visual and bounded |
| Propagation cards | Show injection → expected → actual → containment/recovery | Replaces terminal-only failure inspection |
| Reliability envelope | Shows outcomes, containment, recovery, latency, integrity, and model calls | Connects experiment behavior to measured summary evidence |
| Security catalog | Reports fourteen deterministic cases, categories, and expectations | Makes selectable suite scope server-owned |
| Security controller | Runs confirmed selected cases in a unique stub database and retains JSON | Adds fresh visual security-suite execution |
| Attack table | Shows defense result, expected attack boundary, observed action, redacted evidence, and duration | Makes blocked actions inspectable and filterable |
| Scope boundary | Labels PASS as bounded regression evidence and maturity as partial | Prevents certification or penetration-test claims |

## New Demonstrable Capability

An operator can visually launch isolated fault/security experiments, compare
expected and actual outcomes, inspect propagation and recovery, filter blocked
actions, and verify integrity/zero-real-model-call evidence while the serving
runtime remains running and unarmed.

## Files Added

- `apps/web/src/components/chaos/ChaosSecurityLab.tsx`
- `apps/web/src/styles/chaos-security.css`
- `apps/web/scripts/stage23-smoke.mjs`
- `benchmarks/results/stage14-security-20260825T143324Z-bb0499a1157948a2b4c508e598bea92b.json`
- `benchmarks/results/stage23-chaos-security-20260825T143324Z.json`
- `docs/adr/0023-server-catalogued-confirmed-experiment-ui.md`
- `docs/stages/stage23-chaos-security-lab-ui.md`

## Files Modified

- Loopback service, HTTP adapter, OpenAPI description, security catalog, and API tests.
- Frontend API types/client, route composition, identity, fixtures, tests, manifest, and lockfile.
- Project state, README, architecture, development, repository, ADR index, and risk documentation.

## Tests Performed

- Confirmed API catalog/execution/isolation/retention coverage.
- Chaos maximum-selection, confirmation, propagation, recovery, and summary component coverage.
- Security retained-result, confirmed execution, filtering, blocked-action, and disclaimer coverage.
- Route-specific automated axe scans for Chaos and Security plus all prior workbench routes.
- Real Vite proxy/API run with three selected faults and all fourteen security cases.
- Complete backend regressions, frontend regressions, Python compile, production build, bundle gate, and diff hygiene.

## Measurements

- Real catalog retrieval: 10.376 ms; complete Stage 23 smoke: 7,390.419 ms.
- Chaos HTTP: 4,725.132 ms; report: 4,716.702 ms; three injections and 3/3 expected outcomes.
- Chaos containment: 2/3 (66.667%); the known database-result atomicity gap was reproduced honestly.
- Crash recovery: 1/1 successful; P95 added latency 1,048.260 ms; integrity `ok`; zero real model calls.
- Security HTTP: 2,594.815 ms; suite: 2,355.228 ms; 14/14 PASS, zero failures/model calls, integrity `ok`.
- Frontend tests: 28/28, 9.75 seconds test time; backend tests: 150/150, 41.922 seconds.
- Production build: 219 modules; 130,676 gzip JavaScript bytes (51.0% of the 256,000-byte gate) and 8,333 gzip CSS bytes.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| Fault selection | Select configured scenarios | Delivered from server catalog, capped at three |
| Controlled launch | Require deliberate execution | Delivered with literal confirmation and isolated POST |
| Failure propagation | Compare expected and actual | Delivered per scenario with typed state/error path |
| Recovery behavior | Show attempts and outcomes | Delivered with summary and scenario evidence |
| Security execution | Launch bounded suite | Delivered for selected known cases with retained JSON |
| Attack/blocked results | Inspect defensive behavior | Delivered with category filter and redacted evidence |
| Security claim | Preserve scope | Delivered as bounded regression evidence, not certification |
| Serving runtime | Remain unchanged | Delivered; runtime remained running and integrity `ok` |

## Problems / Technical Debt

- The terminal-state/output atomicity gap still makes database-result failure uncontained.
- Experiment POSTs are synchronous and have no idempotency key or campaign queue.
- Security execution is application-level deterministic testing, not OS sandboxing or penetration testing.
- Retained result selection is filename-time ordered rather than indexed metadata.
- Manual computed contrast, zoom/reflow, forced-colors, and screen-reader validation remains.
- Windows teardown can log the tracked disconnected-client traceback during active polling.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` records Stage 23 complete, the new catalog/execution boundary,
measurements, known containment/security limits, evidence, and Stage 24 approval gate.

## Next Stage

Stage 24 — Advanced Interaction & Motion Polish. No Stage 24 implementation was started.
