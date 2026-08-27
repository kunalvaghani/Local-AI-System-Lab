# Current Project State

## Active Project

Local AI Systems Lab — a fully local, inspectable AI runtime/platform for constrained consumer hardware.

## Current Milestone

The complete local product is a Stage 26 release candidate for the measured
single-user loopback portfolio scope. Stages 17–25 deliver the Systems Cartography
workbench, real Runtime/Agent/Scheduler/Trace/Replay/Hardware/Metrics/Chaos/
Security views, interaction polish, responsive reflow, accessibility semantics,
and bounded rendering. Stage 26 adds the server-catalogued Safe Tool Probe and
one retained acceptance gate across the real local model, built browser client,
API, runtime, scheduler/router/model, tool policy, SQLite, telemetry, trace/replay,
visible failure/recovery, and post-restart rendering. All mandatory categories
pass while overall maturity remains honestly `PARTIAL` and remote multi-user
deployment remains `DEFERRED`.

## Current Stage

Stage 26 — End-to-End Product Verification — COMPLETE, AWAITING APPROVAL.

## Current Subsystem

Verified local React/TypeScript/Vite workbench and loopback backend covering real
runtime, agent, scheduler, trace/replay, source-labelled hardware/performance,
controlled chaos/security, and a server-catalogued exact-grant read-only tool
probe. Stage 26 owns isolated ports/data/processes, combines real-model and full
regression gates, verifies eight browser routes plus five failure statuses, and
normalizes completed inference evidence for rendering after API restart.

## Last Completed Work

- Added strict Stage 26 product acceptance policy and a retained orchestrator that combines the complete Stage 16 real-model gate, frontend tests/build/bundle, isolated random-port API/preview/Chromium flow, exact failures, accessibility automation, and API-restart recovery.
- Added server-owned `GET /v1/tools` and bounded `POST /v1/tools/execute` plus a Runtime Safe Tool Probe that preserves exact agent grants, read-only/path restrictions, typed arguments, persistence, telemetry, and redacted trace/replay.
- Normalized persisted inference task results to the live API shape and reconstructed state history so a URL-selected completed task renders after process restart.
- Verified eight real routes, visible API disconnect/reconnect, inference and tool traces/replay, and exact 400/403/400/409/404 failure responses with zero browser page/console errors or automated A/AA violations.
- Retained `stage26-product-acceptance-20260827T101438Z.json`: 154 backend tests, 39 frontend tests, all Stage 16/26 required categories PASS, one real model call, 150,997-byte gzip JavaScript, SQLite integrity `ok`, and release candidate true/overall `PARTIAL`.
- Added Stage 26 report, ADR-0026, development/architecture/repository/risk updates, and frontend identity 0.26.0; Stage 27 remains unimplemented.

- Added a root `setup_and_run.bat` operational launcher that verifies the local prerequisites, prepares missing pinned llama.cpp/Qwen and frontend dependencies, waits for the backend before starting Vite, reuses matching healthy services, refuses to terminate unknown port owners, and keeps Ollama explicit and separate through `--with-ollama`; this is a Stage 25 usability improvement and does not enter Stage 26.
- Verified the local workbench at 1440×900, 1024×768, 768×1024, 390×844, and 320×568; page client/scroll widths matched after layout settling, with only the intentional mobile route rail scrolling horizontally.
- Replaced viewport-only Runtime task-grid behavior with inline-size container reflow and removed the fixed body minimum width that caused 320 px page overflow.
- Added a stable `Navigate workspaces` accessible name, explicit focus return after command dismissal, explicit skip-to-main focus, one polite atomic API status, and `aria-busy` across the parallel Runtime loading boundary.
- Corrected slow-initial-load task copy so a disabled button remains `Launch task` rather than falsely reporting `Submitting…` before a mutation begins.
- Raised the faint-text token to `#7b8476`; calculated contrast now measures 4.99:1 on canvas and 4.81:1 on the primary panel, with all nine tracked text/focus pairs passing.
- Batched lifecycle SSE presentation once per animation frame while preserving immediate task/end reconciliation, event deduplication, 200-event retention, and 30-row rendering.
- Added four focused Stage 25 tests plus all existing regressions: 38/38 passed, including skip/focus, command focus return, slow backend, 500-event/one-frame/200-retained streaming, 10,000-step/100-row traces, reduced motion, and route axe scans.
- Retained `stage25-responsive-accessibility-performance-20260826T182119Z.json`: twelve route 200s, 37.401 ms median route retrieval, 34.123 ms health retrieval, nine passing contrast pairs, runtime running, integrity `ok`, and 87.819 ms complete smoke.
- Final Stage 25 production build passed at 150,118 gzip JavaScript bytes (58.6% of the 256,000-byte gate) and 9.43 KiB gzip CSS; no dependency was added.
- Added Stage 25 report, ADR-0025, development/architecture/repository/risk updates, and frontend identity 0.25.0; Stage 26 remains unimplemented.

- Added a React Aria command palette for all twelve routes with `Ctrl/Cmd+K` and `/` invocation, filtering, focus management, keyboard action, editable-control protection, and selected-task URL retention.
- Added stable-browser `document.startViewTransition` progressive enhancement around the owned History API commit, naming only the route heading, active rail item, and contextual evidence pane.
- Added explicit reduced-motion bypass and existing tokenized 120/180 ms CSS entry/press/status feedback; no looping or ambient motion was introduced.
- Upgraded the evidence pane with domain/route/task/source facts, progressive shortcut/resize disclosure, and an explicit reset for the existing responsive inspector split.
- Evaluated and rejected/deferred spring physics, animated numbers, arbitrary docking, another virtualizer, canvas/WebGL, cmdk, and a motion runtime because no measured route justifies them.
- Added six focused Stage 24 tests plus all existing regressions: 34/34 passed, including open-palette axe, View Transition, reduced-motion, context, and editable-control cases.
- Retained `stage24-interaction-motion-20260826T155934Z.json`: six route 200s, 24.46 ms median route retrieval, 26.329 ms health retrieval, runtime running, integrity `ok`, and 58.705 ms total smoke.
- Final Stage 24 production build passed at 149,836 gzip JavaScript bytes (58.5% of the 256,000-byte gate) and 9.36 KiB gzip CSS; the JavaScript delta is 19,160 bytes/14.7% from Stage 23.
- Added Stage 24 report, ADR-0024, development/architecture/repository/risk updates, and frontend identity 0.24.0; Stage 25 remains unimplemented.

- Activated `/chaos` and `/security` as real specialist routes backed by server-owned catalogs rather than duplicated browser scenario IDs.
- Added `GET /v1/chaos` and `GET/POST /v1/security`; confirmed experiments accept only known IDs, use separate deterministic stub runtimes/unique databases, and leave the serving runtime unarmed.
- Added maximum-three chaos selection, explicit isolation confirmation, measured reliability summaries, and per-scenario injection → expected → actual → containment/recovery projections.
- Added selected fourteen-case security execution, atomic retained JSON evidence, defensive summaries, category filtering, attack/blocked-action tables, integrity/model-call evidence, and repeated non-certification scope.
- Added 28 frontend tests with eight route-specific axe scans plus API catalog/confirmation/execution/isolation/retention coverage; React review split route query ownership and narrowed completion live announcements.
- Retained `stage23-chaos-security-20260825T143324Z.json`: 3/3 expected chaos outcomes, 2/3 containment with the known persistence gap, 1/1 recovery, 14/14 security defenses, zero real model calls, and serving-runtime integrity `ok`.
- Stage 23 real smoke measured 10.376 ms catalog retrieval, 4,725.132 ms chaos HTTP, 2,594.815 ms security HTTP, and 7,390.419 ms total.
- Final Stage 23 validation passed 150 backend tests in 41.922 seconds, 28 frontend tests in 9.75 seconds, Python compile, the production build, and the 130,676-byte gzip JavaScript gate (51.0% of budget); CSS measured 8,333 gzip bytes.
- Added Stage 23 report, ADR-0023, development/architecture/repository/risk updates, and frontend identity 0.23.0; Stage 24 remains unimplemented.

- Activated `/hardware` and `/metrics` as two real entry points to one source-labelled Hardware & Performance Lab without adding chart, graph, router, motion, or browser-storage dependencies.
- Added semantic CPU topology, RAM pressure, GPU utilization/temperature, and VRAM pressure projections with confidence/source labels and no semantic-zero fallback for missing meters.
- Added selected-task → sampled P50 → matching retained benchmark precedence for TTFT and generation throughput, plus task/distribution queue delay and current scheduler completed/submitted evidence.
- Added a sample-counted eight-metric P50/P95/max table, exact reported model/profile/configuration and workload budget, availability-gated model candidates, and bounded eight-task duration trends.
- Changed browser metrics retrieval to `live=false` because dedicated hardware and scheduler queries already own live refresh, eliminating duplicate hardware probes.
- Added 23 frontend tests with Runtime/Agents/Scheduler/Traces/Hardware/Metrics axe scans and explicit hardware source, null, distribution, model, budget, and history coverage.
- Retained `stage22-hardware-performance-20260825T133404Z.json`: real Ryzen/RTX evidence, 789.314 ms hardware profile, one completed durable stub task, 7.058 ms metrics collection, and 1,610.033 ms total smoke.
- Final Stage 22 validation passed 150 backend tests in 40.544 seconds, 23 frontend tests in 7.95 seconds, Python compile, the production build, and the 127,686-byte gzip JavaScript gate (49.9% of budget); CSS measured 7,365 gzip bytes.
- Added Stage 22 report, ADR-0022, development/architecture/repository/risk updates, and frontend identity 0.22.0; Stage 23 remains unimplemented.

- Activated `/traces` as a real selected-task Trace Explorer using the existing safe trace API, with live polling only while the task is active.
- Added an ordered semantic execution timeline, model/tool/state/failure classification, determinism and component filters, deferred search, exact timestamp-gap bars, and 100-row pages.
- Added validated optional `?step=` URL selection and expandable actor/component/state/model/hash/chain/safe-failure evidence while preserving API payload redaction.
- Added explicit deterministic replay with integrity, reconstructed state, aggregate counts, and per-step matched/diverged/observed/skipped/integrity outcomes; model/tool side effects are never re-executed.
- Kept unsupported cross-run comparison explicit instead of fabricating a browser-derived divergence result.
- Added 18 frontend tests with Runtime/Agents/Scheduler/Traces axe scans and a 10,000-step fixture proving the timeline renders 100 rows per page.
- Retained `stage21-trace-replay-20260825T130714Z.json`: completed 16-step redacted trace, 19.362 ms retrieval, valid 29.216 ms replay, 11 matched, five observed, zero divergence/integrity failure, and 841.405 ms total smoke.
- Final Stage 21 validation passed 150 backend tests in 36.857 seconds, 18 frontend tests in 6.94 seconds, Python compile, the production build, and the 124,662-byte gzip JavaScript gate (48.7% of budget); CSS measured 6,393 gzip bytes.
- Added Stage 21 report, ADR-0021, development/architecture/repository/risk updates, and frontend identity 0.21.0; Stage 22 was still unimplemented at that boundary.

- Activated real `/agents` and `/scheduler` specialist routes without adding graph, chart, router, motion, or persistence dependencies.
- Added agent role/capability/tool inspection, selected-owner highlighting, durable/live state paths, and an ordered intake/agent/admission/scheduler/outcome flow.
- Added worker occupancy, FIFO/priority queue projection, selected-request placement/timings, bounded 50-row reported request ledger, outcome metrics, and reused cancellation controls.
- Preserved the validated selected task across native Runtime/Agents/Scheduler navigation and retained modifier-link/browser history behavior.
- Added live-snapshot-to-retained-metadata fallback for completed scheduler requests while leaving absent stub admission explicitly not reported.
- Added 12 passing frontend tests, including separate Runtime/Agents/Scheduler axe scans, and retained `stage20-agent-scheduler-20260825T124614Z.json` with 15 lifecycle events, five state transitions, 0 ms queue wait, 50.385 ms scheduler execution, and 770.484 ms total.
- Final Stage 20 validation passed 150 backend tests in 40.317 seconds, 12 frontend tests in 5.43 seconds, Python compile, the production build, and the 121,569-byte gzip JavaScript gate (3.1% above Stage 19, 47.5% of budget); CSS measured 5.54 KiB gzip.
- Added Stage 20 report, ADR-0020, development/architecture/repository/risk updates, and frontend identity 0.20.0; Stage 21 was still unimplemented at that boundary.

- Added a typed `/v1` envelope client and TanStack Query 5.102.3 ownership for health, agents, scheduler, hardware, models, metrics, selected-task polling, launch, cancellation, cache seeding, and invalidation.
- Replaced the prototype connection state and `/runtime` placeholders with real local API evidence using resource-specific 1/3/5/60-second polling and abortable requests.
- Added a bounded task composer for real agent/workload selection, 4,096-character objectives, and the backend's 30-second task limit.
- Added validated `?task=<id>` URL selection so refreshable task evidence remains separate from browser persistence and server/query state.
- Added a native EventSource adapter with explicit cursor reconnect, event ID/type deduplication, 200-event retention, 30-event ordered text presentation, terminal close, and cache reconciliation.
- Added selected-task output, error, durable state, inference evidence, request-ID errors, and cooperative cancellation while preserving null/unavailable values and explicit zero real LLM calls.
- Added seven passing component tests for live evidence fixtures, task launch, URL selection, ordered SSE rendering, cancellation, navigation, preference persistence, and automated axe rules.
- Added a reproducible real Vite-proxy/API/SSE smoke runner and retained `stage19-runtime-command-center-20260825T121824Z.json`: route 200, task 202/completed, 15 lifecycle events, one task event, one end event, 632.633 ms stream, 967 ms total, zero real LLM calls.
- Added the Stage 19 report, ADR-0019, development commands, architecture/repository updates, risks R-58–R-61, and frontend identity 0.19.0 without changing backend execution code.

- Added `apps/web` as a local-only React 19.2/TypeScript/Vite 8 application with exact npm lockfile, strict build projects, `/v1` loopback development proxy, and no deployment configuration.
- Encoded Systems Cartography typography, graphite/warm-neutral surfaces, quiet cool accent, four-pixel spacing rhythm, borders/depth, semantic states, 120/180 ms motion, reduced-motion, forced-color, density, and responsive tokens in project-owned CSS.
- Added twelve URL-addressable domains grouped as Observe, Investigate, Test, and System; native links retain modifier-click, browser back/forward, deep-route, and `aria-current` behavior without a routing dependency.
- Added the reusable system bar, domain rail, route workspace, evidence pane, status token, responsive resizable inspector, density selector, and interactive `/design-system` foundations/states/visualization route.
- Defined eleven explicit operational/maturity states: healthy, active, queued, warning, critical, blocked, partial, deferred, unavailable, stale, and unknown.
- Persisted only the versioned device-local density preference; runtime data, task state, and security evidence remain absent from browser storage.
- Rendered real future endpoint contracts plus `Not requested` instead of simulated task, queue, model, hardware, trace, metric, chaos, or security values.
- Separated URL, future REST cache, future SSE reducer, viewer, and device-preference ownership so Stage 19 can integrate real API payloads without rebuilding the shell.
- Built the production client at 102,802 gzip JavaScript bytes versus the 256,000-byte limit; CSS was 3.48 KiB gzip and the deep local `/runtime` route returned HTTP 200.
- Passed 5/5 component tests for every domain, URL navigation, status/visualization components, density persistence, no fake telemetry, and zero axe-core automated shell violations with jsdom contrast explicitly out of scope.
- Added the frontend design-system/UI architecture, Stage 18 report, ADR-0018, bundle gate, development commands, repository map, risks R-55–R-57, and stage state without changing the runtime/API implementation.

- Completed fresh 2026-08-25 frontend research with 28 official or canonical references across Google/Material, Chrome and web-platform capabilities, developer/observability interfaces, and maintained open-source React candidates.
- Recommended **Systems Cartography**: a graphite/neutral, data-dense runtime workbench combining an operating-system inspector, profiler, trace debugger, and experiment laboratory without copying Material, a generic dashboard, or a chat interface.
- Mapped proposed interactions to the real `/v1` health, task/SSE, agent, scheduler, hardware, model, metric, trace/replay, chaos, and security-result surfaces.
- Recommended React 19.2, TypeScript, Vite 8, native CSS tokens/Modules, React Aria Components, TanStack Query/Table/Virtual, and react-resizable-panels as the lean core direction.
- Limited React Flow and Recharts to lazy specialized views; preferred native CSS/View Transitions as progressive enhancement; deferred Motion, cmdk, xterm.js, Monaco, WebGL-first rendering, arbitrary docking, SSR/RSC, and generic UI frameworks until evidence justifies them.
- Defined proposed (not yet measured) shell, virtualization, SSE update, chart-point, fixture, INP/long-task/heap, and lazy-loading performance constraints for Stage 18 validation.
- Carried WCAG 2.2 AA, keyboard, reduced-motion, live-region, zoom/reflow, high-contrast, graph/table equivalence, and explicit non-happy-state requirements into the design-system stage.
- Added `docs/frontend-research.md`; updated the README, architecture, repository map, risk register, and project state without adding a frontend directory, dependency, route, component, stylesheet, or production UI.

- Added strict Stage 16 acceptance policy for a 150-test floor, 14 security cases, nine chaos scenarios, 100% expected chaos/recovery rates, minimum 75 tok/s, maximum +50% TTFT regression, 1,600 MiB RAM, 1,500 MiB VRAM delta, and 10-second real API stream.
- Added a reproducible runner covering compile/package, the complete suite, targeted cancellation/timeout and malformed-output tests, scheduler, hardware/admission, killed-process recovery, trace/replay, observability, chaos, security, deterministic API, and real-model API.
- Added SHA-256 command-output evidence, embedded acceptance thresholds, retained subsystem summaries, Stage 2 regression arithmetic, and a nonzero exit contract for mandatory failure.
- Retained `stage16-backend-acceptance-20260825T011603Z.json`: 14/14 commands exit 0, 14/14 required categories PASS, zero FAILED subsystems, release candidate true, recommendation to accept for single-user loopback frontend work with tracked limitations.
- Ran 150 tests in 39.115 seconds; eight targeted cancellation/timeout tests and six focused malformed-output/fault tests also passed.
- Recovered an actually terminated worker to `completed` with zero model calls and integrity `ok`; trace replay matched with zero deterministic divergences; observability unified four tasks, one recovery, and 55 steps.
- Re-ran all nine chaos scenarios: 9/9 expected outcomes and recovery 1/1, while honestly retaining 8/9 containment due to the known terminal-output atomicity gap.
- Re-ran all fourteen bounded security cases: 14/14 PASS, zero failures/model calls, integrity `ok`; security maturity remains `PARTIAL`, not certified.
- Re-ran deterministic and real separate-process APIs: 16 operations each, zero/one model calls, integrity `ok`.
- The real Stage 16 API run used Qwen2.5 1.5B/`performance`: 2,375.728 ms total, 1,747.839 ms TTFT, 93.68 tok/s, 1,343.895 MiB RAM, 1,189 MiB VRAM, and 4,589.371 ms HTTP/SSE stream.
- Passed all five regression limits: throughput, TTFT (+3.616% from Stage 2 median), RAM, VRAM, and API stream duration.
- Classified core runtime, scheduler/admission, trace/replay/observability, and backend API `DONE`; persistence/recovery, fault injection, security, and model routing/evaluation `PARTIAL`; remote multi-user deployment `DEFERRED`.
- Added the Backend Acceptance Report, Stage 16 report, ADR-0017, strict config/classifier tests, and package identity 0.16.0 without adding frontend code.

- Added strict tracked API configuration: literal loopback binding, 64 KiB request cap, eight in-flight tasks, 30/45-second default/maximum task deadlines, 50 ms SSE polling, 45-second stream cap, and three-scenario chaos cap.
- Added a transport-independent service integrating tasks, agents, scheduler, hardware, model registry/budgets, unified metrics, redacted traces, replay, chaos, and retained security results.
- Added bounded asynchronous API task ownership with cooperative cancellation, terminal status mapping, clean shutdown, and durable completed-task fallback inspection after restart.
- Added dependency-free HTTP/1.1 JSON and SSE over `ThreadingHTTPServer`, strict UTF-8/JSON/media-type/query/field validation, duplicate-key/non-finite rejection, typed error mapping, request IDs, no-store/security headers, and no static file serving.
- Added `/v1` discovery/health/OpenAPI, task create/inspect/cancel/events/trace, component inspection, trace inspect/replay, confirmed isolated chaos, and security-result routes.
- Omitted system prompts, absolute model paths, trace raw input/output payloads, and trace-run metadata from safe inspection surfaces.
- Required literal chaos confirmation and ran at most three unique scenarios through a separate stub runtime and unique database, leaving the serving runtime unarmed.
- Retained `stage15-api-20260824T205654Z.json`: 16 external HTTP/SSE operations, zero post-launch direct runtime calls, zero real LLM calls, completed durable task, 15 lifecycle events, 16 redacted trace steps, valid replay, expected isolated chaos, zero security failures, and integrity `ok`.
- Retained `stage15-api-real-20260825T010429Z.json`: the same 16-operation workflow through Qwen2.5 1.5B/llama.cpp with one real model call, completed durable task, 18 SSE lifecycle events, 19 redacted trace steps, valid replay, isolated chaos, zero retained security failures, and integrity `ok`.
- The real external task used the admitted `performance` profile and measured 2,973.505 ms inference, 2,210.807 ms TTFT, 103.32 tok/s, 1,343.887 MiB peak child RAM, and 1,189 MiB VRAM delta.
- Added `local-ai-api`, Stage 15 external runner, ADR-0016, Stage 15 report, and nine real-socket API tests including strict bind/config validation, active cancellation, and post-restart durable inspection.

- Added strict Stage 14 policy for 4,096-character objectives, depth-six/256-node payloads, 8,000-character model output, 20,000-character tool output, 45-second subprocess timeout, and one process slot.
- Added pre-persistence validation for JSON-like structure, finite numbers, control characters, size bounds, sensitive field names, and token/bearer/private-key patterns.
- Added JSON-encoded `UNTRUSTED_USER_OBJECTIVE` prompt separation while keeping tool, network, path, and subprocess authority in deterministic code outside the model.
- Replaced raw objective lifecycle data with objective hash/length and added recursive secret redaction for event/metric payloads.
- Strengthened filesystem reads with configured allowed entries, denied components, suffix allowlists, resolved containment, and symlink-escape rejection.
- Added a global read-only `filesystem.read` permission ceiling above existing exact agent grants; no shell, network, process, write, or escalation tool is registered.
- Added deny-by-default application network policy, exact no-shell subprocess validation, bounded arguments/timeouts, secret-free argv, and one-slot guarded inference.
- Retained `stage14-security-20260824T203349Z.json`: 14/14 PASS, zero FAIL, 2,181.687 ms, zero real LLM calls, and SQLite integrity `ok`.
- Retained five runtime tasks (one completed, three security-blocked, one tool-failed), one stub model call, three tool calls, five trace runs, 55 steps, and a 6.242 ms observability query.
- Added `local-ai-security`, Stage 14 runner, ADR-0015, Stage 14 report, and 10 focused security tests while explicitly refusing to call the system secure.
- Ran the guarded Stage 14 runtime against real Qwen2.5 1.5B: one completed task/model call, one prompt-protection event, zero faults, 19 trace steps, 3,370.565 ms inference, 2,760.402 ms TTFT, 105.39 tok/s, 1,343.949 MiB RAM, and 1,189 MiB VRAM.

- Added nine strict fault scenarios covering model/tool timeout, invalid model output, context overflow, simulated OOM, corrupted tool result, malformed tool call, terminal database-result failure, and agent crash/recovery.
- Added disabled-by-default, explicitly armed plans with scenario selection, maximum 1,000 ms configured delay, positive injection caps, unique IDs, and no probabilistic behavior.
- Added a thread-safe controller that records one task-correlated `fault.injected` metric per activation.
- Added protocol decorators around inference, tool execution, and terminal result persistence without adding chaos branches to `AgentRuntime`.
- Added an actual subprocess termination after `recovery_ready`; a fresh runtime recovered the same task through `RECOVERING` with zero real LLM calls.
- Retained `stage13-chaos-20260824T193424Z.json`: nine injections, 9/9 expected outcomes, 8/9 contained, one recovery/one success, SQLite integrity `ok`, 11 trace runs/140 steps.
- Reproduced R-32: a terminal result-save failure returns `database_operation_failed` while state remains `completed` and no output row exists; the report correctly marks it not contained.
- Added `local-ai-chaos`, Stage 13 runner, ADR-0014, Stage 13 report, and 11 focused fault tests.
- Ran the normal Stage 13 runtime against the real Qwen2.5 1.5B backend: one completed task/model call, zero injected faults, 2,410.179 ms inference, 1,693.755 ms TTFT, 102.59 tok/s, 1,343.566 MiB RAM, and 1,185 MiB VRAM.

- Added a typed `ObservabilityBackend` and Stage 12 real/stub factory composition without changing SQLite schema v2.
- Added one consistent windowed SQLite read transaction across task state, metric events, outputs, tool calls, recovery attempts, traces, and replay reports.
- Added task/activity totals and count/min/P50/P95/max/mean distributions for task, queue, scheduler, tool, recovery, inference, TTFT, throughput, RAM, and VRAM evidence.
- Added bounded recent-task/event drill-down connecting run, agent, model, route, scheduler, hardware, failure, recovery, and trace evidence.
- Added optional live scheduler and source/confidence-labelled hardware snapshots; unavailable samples remain `null` with count zero.
- Defined reported retries truthfully as recovery attempts because no independent generic retry subsystem exists.
- Retained `stage12-observability-20260824T163054Z.json`: four tasks, three completions, one expected failure, two model calls, one tool call, one recovery/retry, four trace runs, and 55 trace steps.
- Ran real Stage 12 Qwen inference and queried it after restart: one completed task/model call/route, 18 trace steps, 2,927.102 ms total, 2,238.325 ms TTFT, 96.16 tok/s, 1,343.703 MiB RAM, and 1,189 MiB VRAM.
- Added `local-ai-observe`, Stage 12 runner, ADR-0013, Stage 12 report, and 9 focused observability tests.

- Migrated SQLite forward from schema v1 to v2 with trace runs, ordered trace steps, and persisted replay reports.
- Added stable per-run UUID step identities, UTC timestamps, actor/component ownership, canonical input/output hashes, normalized semantic hashes, state/model/configuration/failure metadata, and previous/envelope hashes.
- Classified each traced event as deterministic, nondeterministic, observational, or side-effecting.
- Added hashed model prompt/configuration/output boundaries while explicitly classifying generation as nondeterministic.
- Added side-effect-free replay that verifies the full trace chain and reconstructs legal state transitions without new model calls or repeated tool operations.
- Added cross-run comparison with deterministic matches/divergences, nondeterministic observations, missing events, and model/configuration equality.
- Added trace loading after restart plus CLI `demo`, `inspect`, `replay`, and `compare` operations.
- Retained `stage11-trace-replay-20260824T143744Z.json`: two 15-step runs, 10 deterministic matches, zero divergences, five nondeterministic observations, replay state `completed`, integrity `ok`.
- Ran real Stage 11 Qwen inference and replay: 18 trace steps, 11 deterministic matches, seven observed-only steps, reconstructed `completed`, no regeneration, integrity `ok`.
- Added `local-ai-trace`, Stage 11 runner, ADR-0012, Stage 11 report, and 9 focused tracing tests.

- Added SQLite schema version 1 for agents, tasks, state transitions, checkpoints, lifecycle events, metric events, execution steps, model configurations, tool calls, outputs, and recovery attempts.
- Added validated persistence configuration with foreign keys, 5,000 ms busy timeout, WAL journaling, and `FULL` synchronous durability.
- Added narrow SQLite agent, lifecycle, metric, checkpoint, and task-state adapters over one shared runtime store.
- Kept the Stage 4 legal graph authoritative and added explicit `RECOVERING -> PLANNING`; illegal SQLite transitions roll back without partial state.
- Added explicit `recovery_ready` checkpoints only in `PLANNING`, before model/tool invocation begins.
- Added recovery classification for recoverable, terminal, unsafe in-flight, and invalid-checkpoint tasks.
- Added a durable recovery-attempt ledger and refused automatic retries for terminal or ambiguous side-effect boundaries.
- Persisted model configuration at runtime start, tool requests/results/errors, inference/tool outputs, and task/event timestamps.
- Demonstrated an actual worker process killed after its committed checkpoint and a fresh runtime completing the original task through `RECOVERING`.
- Retained `stage10-recovery-20260824T131728Z.json` with schema version, row counts, state history, output, and `integrity_check: ok`.
- Ran real Stage 10 Qwen inference and reconstructed its completed state/five transitions from SQLite without starting the model.
- Added `local-ai-recovery`/`runtime.recovery_cli`, Stage 10 runner, ADR-0011, Stage 10 report, and 11 focused tests.

- Added a typed, versioned registry for model identity, artifact/backend availability, capabilities, token limits, minimum memory, latency class, quality rank, and benchmark provenance.
- Registered the installed Qwen2.5 1.5B baseline and an explicitly unavailable/unbenchmarked optional Qwen2.5 0.5B candidate without fabricating a second real local artifact.
- Added an explainable workload router using task type, complexity, context/output size, latency, queue depth, live memory, task budgets, and historical benchmark evidence.
- Retained every candidate acceptance/rejection and scoring reason in route lifecycle/result evidence.
- Added interactive, standard, and background compute-budget defaults covering maximum inference calls, generated tokens, total time, RAM, and VRAM.
- Enforced zero-call rejection, native token capping, remaining-time scheduler capping, and exact-profile estimated RAM/VRAM limits before scheduler submission.
- Demonstrated a 600 MiB VRAM budget automatically skipping larger profiles and selecting the admitted `constrained` profile.
- Added post-execution usage evidence for calls, generated token runs, elapsed time, peak child RAM, and VRAM delta.
- Demonstrated controlled interactive explanation routing to the compact candidate and standard risk analysis routing to the 1.5B model for an exact capability reason.
- Demonstrated truthful live routing to the only installed/configured model, with the compact candidate rejected for missing artifact/backend.
- Ran real interactive and background Stage 9 Qwen executions, including different profile and token-budget choices.
- Added `local-ai-routing`/`runtime.routing_cli`, a retained Stage 9 route result, ADR-0010, Stage 9 report, and focused tests.

- Added four typed, tracked inference profiles controlling context, batch/ubatch, generation/batch threads, GPU layers, flash attention, and device selection.
- Preserved the exact Stage 7 configuration as `performance`; labelled every alternative an experimental hypothesis rather than an optimum.
- Added workload-specific profile order: interactive/standard prefer performance, while background prefers balanced.
- Added `AdaptiveInferenceController`, which captures one fresh snapshot, evaluates candidates in order, and selects only the first profile receiving `ACCEPT`.
- Reuses Stage 7 estimation/admission for every candidate; a recommendation never bypasses re-admission or reaches native inference directly.
- Added request-scoped llama.cpp flags for all seven controlled parameters while retaining `--fit off`.
- Added lifecycle/result evidence for every attempted profile, exact selected/applied profile, hardware snapshot, admission, reason, scheduler, and inference metrics.
- Demonstrated controlled pressure selecting balanced after performance queued, missing GPU selecting CPU-safe, and missing RAM blocking all work before the scheduler.
- Ran the same real workload through performance, balanced, constrained, and CPU-safe profiles and retained the raw JSON result.
- Demonstrated live standard selecting performance and live background selecting balanced through the full agent runtime.
- Added `local-ai-adaptive`/`runtime.adaptive_cli`, Stage 8 benchmark runner, ADR-0009, and Stage 8 report.

- Added source/confidence-labeled CPU identity, logical processor, RAM capacity/availability, GPU, VRAM pressure, utilization, temperature, driver, and compute-capability profiling.
- Preserved unavailable physical-core evidence as `null` with a warning rather than fabricating it from the 16 logical processors.
- Added validated model metadata from the actual 1,117,320,736-byte pinned GGUF file and explicit estimator coefficients/reserves.
- Added a transparent host/VRAM estimator with component-level arithmetic, assumptions, and medium/low confidence labels.
- Compared the exact baseline prediction against the retained real Stage 6 peak: RAM +122.643 MiB/+9.158%; VRAM +17.116 MiB/+1.404%.
- Added inspectable `ACCEPT`, `QUEUE`, `REDUCE_CONTEXT`, `REDUCE_GPU_OFFLOAD`, `FALLBACK`, and `REJECT_UNSAFE` decisions.
- Added a pre-scheduler admission gate: only `ACCEPT` invokes the scheduler/backend; other outcomes raise structured `admission_controlled` and enter terminal `RESOURCE_BLOCKED`.
- Added `local-ai-hardware`/`runtime.hardware_cli`, controlled coverage of all six branches, ADR-0008, and the Stage 7 report.

- Added typed scheduler policies, workload classes, priorities, request statuses, options, handles, results, snapshots, and aggregate metrics.
- Added `QueuedScheduler` with configurable bounded workers and stable FIFO or priority selection.
- Added interactive, standard, and background default priorities of 100, 50, and 10 with explicit priority override support.
- Added wait-time aging plus an oldest-request maximum-wait promotion to prevent indefinite background starvation while workers make progress.
- Added an independent queue monitor so queued cancellation and expiry occur even while all workers are busy.
- Added end-to-end deadlines spanning queue wait and operation execution; active expiry signals the cooperative backend token.
- Added cancellation for queued and running logical requests and mapped scheduler cancellation/timeout to `CANCELLED`/`TIMEOUT` task states.
- Added queue metrics for current/running/peak depth, outcomes, P50/P95/max wait, execution order, and starvation promotions.
- Routed real `AgentRuntime` inference through one priority worker, matching the current backend's single-process limit.
- Added scheduler request lifecycle events and per-result request ID, workload, priority, queue wait, execution time, status, and timestamps.
- Extended inference `generate()` with cancellation so scheduler control reaches the owned llama.cpp process.
- Added locks to process-local agent, event, checkpoint, and metric stores for concurrent Stage 6 callers.
- Demonstrated the same submissions as FIFO `background -> standard -> interactive` and priority `interactive -> standard -> background`.
- Demonstrated a real Technical Explainer/Qwen run through the Stage 6 scheduler.
- Added the `local-ai-scheduler`/`runtime.scheduler_cli` comparison, ADR-0007, Stage 6 report, and ordering/control/concurrency tests.

## Currently Working On

None. Stage 26 is complete and work is stopped before Stage 27 Product Demonstration & Portfolio Packaging.

## Current Blockers

- User approval is required before Stage 27 Product Demonstration & Portfolio Packaging.
- No runtime/API blocker prevents the next single-user loopback frontend scope.
- The API has no list-tasks endpoint; Stage 19 truthfully inspects only the selected known/created task.
- Stage 20/21 visualize one selected task and do not claim a global task explorer.
- Stub tasks report no admission decision, so Stage 20 truthfully displays `Not reported`; real admitted runs expose the retained decision.
- The API has no safe cross-run trace-comparison endpoint; Stage 21 exposes only source-run replay divergence.
- The selected trace API returns all steps; the UI bounds its DOM to 100 rows and verifies a 10,000-step fixture, but server-side pagination remains future work.
- CPU utilization and continuous hardware history are not backend contracts; Stage 22 shows topology and bounded recent tasks instead.
- Exact applied profile configuration appears only when selected-task result metadata reports it; stub tasks legitimately leave it unavailable.
- Chaos/security execution is synchronous, has no idempotency key or campaign history API, and may occupy a local HTTP worker for several seconds.
- The known terminal-result/output atomicity gap remains visible as an uncontained database-result fault; Stage 23 does not repair it.
- Security PASS evidence is bounded deterministic regression evidence, not a penetration test, OS sandbox, certification, or proof of security.
- Stage 25 validates computed token contrast, five viewport sizes, browser accessibility-tree semantics, focus return, and keyboard splitter operation; manual multi-screen-reader, forced-colors, and broad zoom/browser coverage remains future work.
- Real-browser View Transition paint cost, INP, long tasks, and field interaction timing remain unmeasured; Stage 25 retains the immediate/reduced-motion fallback and does not make field-performance claims.
- A second real model artifact/backend is not installed; controlled route differences are therefore policy evidence, not a claim of compact-model inference.
- Python 3.11 on Windows can retain the deliberately faulted SQLite handle through temporary-directory cleanup; the complete verified gate uses the established Python 3.10 runtime.

## Important Decisions

- Follow one stage at a time and stop for explicit approval after each stage.
- Adopt Systems Cartography as the primary direction: dense evidence-first inspection with restrained color/motion, text-equivalent visualizations, and adaptive workspace/evidence panes.
- Keep the web application local-only and client-rendered with React/TypeScript/Vite; preserve the literal loopback backend boundary.
- Use project-owned CSS tokens, React Aria behavior, and one accessible resizable split instead of a visual framework or arbitrary docking system.
- Keep shallow top-level routing on a narrow native-history adapter; adopt a maintained router only when parameterized/nested route behavior justifies its cost.
- Persist only versioned device preferences; never mirror backend runtime evidence into localStorage.
- Require the initial compressed JavaScript shell to stay at or below 250 KiB; record optional dependency deltas before keeping them.
- Prefer a small accessible and virtualized client stack; make graph/chart/motion/editor/terminal dependencies separately measurable and lazy rather than default shell costs.
- Keep URL state, REST/query cache state, SSE lifecycle state, and transient inspector selection state distinct; Stage 19 implements these owners independently.
- Use TanStack Query for deduplicated browser server state and native EventSource for the single selected task; never persist runtime evidence in browser storage.
- Bound the selected task stream to 200 retained/30 rendered lifecycle events and reconnect continuing timeouts only from the explicit cursor.
- Treat every graph, timeline, and chart as a projection of the accepted API, never a second runtime source of truth.
- Separate binary required-category acceptance from `DONE`/`PARTIAL`/`FAILED`/`DEFERRED` subsystem maturity.
- Require every mandatory category to pass for release-candidate status; never let a high aggregate test count substitute for real recovery, chaos, security, API, or model evidence.
- Scope acceptance to the measured single-user loopback backend; remote multi-user deployment remains explicitly deferred.
- Track acceptance thresholds before execution, embed them in the retained result, and require a full rerun when policy changes.
- Stage 26 end-to-end product verification was explicitly approved; Stage 27 product demonstration/portfolio packaging requires its own user approval gate.
- Keep product acceptance isolated on random loopback ports, a unique temporary database, and an owned browser session; never terminate or mutate an unknown development stack.
- Keep tool discovery server-owned and execution exact-grant/read-only/path-restricted; the browser never grants authority.
- Require the real-model Stage 16 sub-gate and deterministic browser sub-gate together; neither substitutes for the other.
- Normalize persisted inference results to the live API contract for restart rendering while retaining the explicit durable envelope for tool-only tasks until a discriminated result union is approved.
- Use component inline-size rather than viewport width when a resizable pane owns the actual layout constraint.
- Reject page-level horizontal overflow at 320 px; keep the grouped mobile route rail as one intentional, contained horizontal scroller.
- Give persistent controls stable accessible names independent of collapsed visible labels, restore command focus explicitly, and announce only coarse connection status rather than flooding lifecycle events.
- Batch high-frequency lifecycle presentation once per animation frame, but flush task snapshots and stream-end events immediately and preserve the 200-event/30-row bounds.
- Keep the existing 100-row trace paging instead of adding a virtualizer while the 10,000-step fixture remains bounded.
- Do not claim WCAG conformance or field Core Web Vitals from axe, calculated token pairs, one Chromium accessibility snapshot, or one-run local route timings.
- Use native View Transitions only as progressive enhancement around shallow route commits, bypass them for reduced motion, and animate only bounded orientation surfaces.
- Use the installed React Aria primitives for the twelve-item command palette; do not add cmdk or another overlapping interaction library.
- Keep the existing responsive two-pane workspace and reset control; arbitrary docking is not justified.
- Do not add spring physics, animated numbers, another virtualizer, canvas/WebGL, or an animation runtime without measured route evidence.
- Keep experiment catalogs server-owned; browser selection may submit only reported known IDs.
- Require explicit confirmation for chaos and security execution, use separate deterministic runtimes/databases, and never arm the serving runtime.
- Label adversarial PASS as an expected defense holding, not certification, and retain the backend disclaimer beside results.
- Keep one owner per live resource: hardware and scheduler poll independently while the metrics projection requests durable-only evidence with `live=false`.
- Preserve performance evidence precedence: selected-task measurement, then sampled distribution, then a matching retained model benchmark labelled retained.
- Never render an unavailable resource meter with a semantic zero and never attach one model's benchmark to a different selected model.
- Treat recent tasks as a bounded durable comparison, not a continuous background hardware time series.
- Preserve the safe trace boundary: display hashes and safe failures, never reconstruct redacted inputs, outputs, run metadata, or failure details.
- Label bars between trace records as timestamp gaps, not component execution latency.
- Trigger replay only by explicit user action and preserve the backend rule that nondeterministic work is observed and side-effecting tools are skipped.
- Keep trace search/filter/page state ephemeral; persist only validated task and expanded-step identifiers in the URL.
- Use versioned loopback HTTP/1.1 with RFC 8259 JSON and SSE because current commands are request/response and execution updates are server-to-client only.
- Keep API operations transport-independent; `AgentRuntime` and its protocols do not depend on a web framework.
- Use the standard-library server only as a local development boundary and reject non-loopback binds; do not describe it as production-ready.
- Bound request bytes, in-flight task count, task/stream duration, and chaos selection; keep scheduler and inference limits authoritative underneath.
- Omit system prompts and raw trace payloads from API views; local SQLite remains sensitive despite boundary redaction.
- Require explicit chaos confirmation and execute only in an isolated stub runtime/database, never the serving runtime.
- Keep critical authorization outside model behavior; prompt instructions and delimiters are defense-in-depth, not security boundaries.
- Treat every objective as untrusted JSON-encoded data and never let it grant tools, network, paths, or process authority.
- Validate detected secrets before persistence/inference and redact runtime telemetry; retain ignored local databases as sensitive because validated task/output text remains durable.
- Permit only configured read-only filesystem entries and globally deny network/shell/process/write permissions until a later approved design adds isolation.
- Validate the pinned subprocess contract with exact executable/cwd, `shell=False`, bounded argv/time, and a one-slot inference ceiling.
- Report each adversarial case as PASS/FAIL with evidence and state explicitly that a passing suite is not a security certification.
- Keep fault plans disabled by default and require explicit CLI arming; configuration, delays, and counts remain bounded and validated.
- Inject at replaceable protocol boundaries instead of scattering chaos conditions through core orchestration.
- Record every activation as task-correlated telemetry and compare expected/actual state and error rather than treating any failure as success.
- Retry only the killed worker at its committed pre-invocation checkpoint; model/tool side-effect boundaries remain terminal.
- Report the reproduced terminal-output transaction gap as uncontained instead of inflating the containment rate.
- Keep Stage 12 pull-based and local: query authoritative SQLite evidence, then attach separately labelled live scheduler/hardware snapshots.
- Preserve missing observations as null statistics with zero sample count; never turn an absent measurement into a zero.
- Define retries as recovery attempts until a distinct retry subsystem exists, and disclose that source in every report.
- Keep SQLite schema v2; aggregation does not justify duplicating authoritative records on the write path.
- Treat one task as one durable trace run; recovery continues that run rather than fabricating a new task history.
- Derive stable step identity from run ID, ordinal, and event name; use canonical hashes plus a previous-hash chain to detect mutation/reordering.
- Replay only deterministic reducers. Observe model/environment evidence and skip tool side effects instead of claiming full behavioral re-execution.
- Compare normalized semantic hashes only for deterministic steps; report nondeterministic evidence separately.
- Treat SHA-256 chains as tamper-evidence, not authentication against an actor who can recompute the database.
- Use explicit JSON and typed reconstruction; never persist runtime objects with pickle.
- Treat the existing legal state graph as authoritative inside SQLite transactions.
- Automatically retry only an exact pre-invocation `recovery_ready` checkpoint; never guess whether model/tool side effects occurred.
- Record `RECOVERING` and recovery attempts durably instead of disguising recovery as a fresh task.
- Reject terminal and in-flight tasks from automatic recovery, preserving them for inspection/manual resolution.
- Use SQLite WAL/FULL with short per-operation connections for the current single-host runtime.
- Define model availability as both artifact presence and configured backend support; aliases and stubs are not counted as real models.
- Retain unavailable candidates and their rejection reasons instead of silently dropping them from route evidence.
- Treat declared capabilities/quality ranks as routing policy metadata, not semantic output-quality proof.
- Enforce call/token/time and estimated memory limits before scheduler submission; report observed peaks separately because sampling cannot retroactively prevent an estimator miss.
- Keep the existing exact-profile admission as the final safety authority after routing.
- Complete and accept the backend before production frontend work.
- Keep important runtime logic framework-independent and inspectable.
- Use Python as the initial implementation language; require measured evidence before introducing C++.
- Treat observed repository state and executed tests as higher-confidence evidence than plans.
- Use Python structural protocols and constructor injection for current component boundaries.
- Keep Stage 1 synchronous and dependency-free until real inference/scheduling requirements provide evidence for async or third-party tooling.
- Use the direct, pinned llama.cpp subprocess path as the first serious baseline; keep Ollama outside this measurement.
- Launch one native process per request in Stage 2 to make streaming, cancellation, cleanup, and cold-load cost explicit.
- Allow only one active inference process per backend instance until scheduler admission/concurrency is implemented.
- Keep all runtime inference offline; permit network access only in the explicit setup/download workflow.
- Resolve specialized agents by registered stable identity; callers do not construct direct backend calls.
- Treat tool capabilities as explicit narrow grants; a name and its required permission set must both match a registered definition.
- Use only coarse direct task states in Stage 3; reserve detailed states, failure variants, and legal-transition enforcement for Stage 4.
- Store lifecycle events separately from performance telemetry; Stage 10 retains both through narrow SQLite adapters.
- Treat task completion and role/output correctness as separate concerns.
- Keep every state change behind the `TaskStateMachine` protocol; runtime branches cannot assign current state directly.
- Treat all failure and completed states as terminal and non-reentrant.
- Record an initialization transition (`None -> CREATED`) so task history is complete from origin.
- Route tool-only success through `WAITING_FOR_TOOL -> VALIDATING -> COMPLETED`; never bypass the shared state machine.
- Keep tool-handler and scheduler request deadlines separate; both are enforced at their owning execution boundaries.
- Permit only vetted, read-only tools under application-level containment; do not claim this is an OS sandbox.
- Use cooperative cancellation tokens for tools and return at the configured deadline; require process isolation before admitting untrusted or side-effecting handlers.
- Default deny a tool unless the executing agent has an exact grant with all required permissions.
- Keep FIFO as an executable baseline and use aged priority for the current serious runtime.
- Use stable sequence ordering for equal effective priorities.
- Treat interactive/standard/background values 100/50/10 as transparent baselines, not measured optima.
- Count the request deadline from submission so queue time cannot escape the budget.
- Run an independent queue monitor so a busy worker cannot prevent queued timeout/cancellation.
- Keep one real scheduler worker; Stage 7 establishes per-request fit but does not prove concurrent inference safe.
- Preserve synchronous `AgentRuntime.run()` for now while the scheduler itself exposes request handles; external async control belongs to the API stage.
- Record scheduler queue evidence in task results and lifecycle metrics without claiming Stage 12 observability.
- Reject only empty output in Stage 4; semantic validators remain future work.
- Attach sources and confidence to resource evidence; never substitute declared hardware for an unavailable live reading.
- Keep estimator arithmetic and safety reserves explicit; treat one exact configuration as medium-confidence and extrapolation as low-confidence.
- Execute only `ACCEPT` in Stage 7. Recommendations require re-evaluation after Stage 8/9 applies a change or pressure clears.
- Distinguish pre-execution `RESOURCE_BLOCKED` from a backend `OUT_OF_MEMORY` failure.
- Use discrete tracked profiles instead of unconstrained runtime parameter mutation.
- Share one fresh hardware snapshot across all candidate attempts so selection compares a coherent pressure point.
- Require `ACCEPT` for the exact selected context/GPU-layer profile before scheduler submission.
- Keep llama.cpp `--fit off`; native code must not silently override the controller's inspectable decision.
- Treat current profile values and workload order as measured policy baselines, never universal optima.
- Keep adaptive profiles model-specific; Stage 9 routes models first and requires a real backend/profile/admission bundle before a second model becomes executable.

See [ADR-0001](docs/adr/0001-stage-gated-modular-backend-first.md), [ADR-0002](docs/adr/0002-typed-protocols-and-stdlib-skeleton.md), [ADR-0003](docs/adr/0003-pinned-llama-cpp-qwen-baseline.md), [ADR-0004](docs/adr/0004-registered-agent-runtime-and-lifecycle-events.md), [ADR-0005](docs/adr/0005-validated-execution-state-machine.md), [ADR-0006](docs/adr/0006-default-deny-bounded-tool-runtime.md), [ADR-0007](docs/adr/0007-bounded-aged-priority-scheduler.md), [ADR-0008](docs/adr/0008-conservative-pre-scheduler-memory-admission.md), [ADR-0009](docs/adr/0009-discrete-re-admitted-inference-profiles.md), [ADR-0010](docs/adr/0010-explainable-availability-gated-model-routing.md), [ADR-0011](docs/adr/0011-sqlite-checkpoints-and-pre-invocation-recovery.md), [ADR-0012](docs/adr/0012-hash-chained-traces-and-bounded-replay.md), [ADR-0013](docs/adr/0013-sqlite-windowed-observability-snapshots.md), [ADR-0014](docs/adr/0014-bounded-protocol-fault-injection.md), [ADR-0015](docs/adr/0015-deterministic-security-boundaries.md), [ADR-0016](docs/adr/0016-loopback-stdlib-http-json-sse-api.md), [ADR-0017](docs/adr/0017-scoped-evidence-based-backend-acceptance.md), [ADR-0018](docs/adr/0018-systems-cartography-web-shell.md), and [ADR-0019](docs/adr/0019-real-loopback-query-and-sse-client.md).

## Tests Passing

- `python -m benchmarks.run_stage26_product_acceptance` — exit 0; release candidate true, all seven Stage 26 and all fourteen inherited Stage 16 required categories PASS, overall maturity `PARTIAL`.
- Stage 26 backend gate — 154/154 tests, complete control/fault/recovery/trace/observability/chaos/security/API coverage, and one real Qwen/llama.cpp inference passed in 91,410.474 ms.
- Stage 26 frontend gate — 39/39 component/axe tests, production TypeScript/Vite build, and 150,997/256,000 gzip JavaScript gate passed.
- Stage 26 browser gate — eight real routes, inference/tool completion, 16-step traces, side-effect-free replay, visible API outage/recovery, zero page/console errors, zero automated WCAG A/AA violations, and restart rendering passed.
- Stage 26 failure gate — invalid task 400, denied cross-agent tool 403, unconfirmed chaos 400, terminal cancellation 409, and missing task 404 matched exactly.
- Focused API/product-policy regression — 5/5 tests passed for tool catalog/execution/denial, durable inference normalization/history, strict acceptance config, full-pass classification, and required-failure rejection.
- Python 3.11 diagnostic — runtime scenarios execute, but the injected SQLite database-failure test hits a Windows temporary-file cleanup handle; this interpreter is not the Stage 26 verified runtime.

- `npm run build` in `apps/web` — strict TypeScript/Vite production build passed in 209 ms; one 389.17 kB raw/119.14 kB reported-gzip JavaScript asset and one 21.80 kB raw/4.66 kB gzip CSS asset.
- `npm test` — 7/7 Stage 19 component tests passed in 4.48 seconds, including real-contract fixtures, task URL selection, lifecycle rendering, cancellation wiring, and the automated axe scan.
- `npm run check:bundle` — PASS; exact initial JavaScript is 117,956 gzip bytes ≤256,000, a +15,154-byte (+14.7%) delta from Stage 18.
- `npm run smoke:stage19` — PASS through real Vite proxy and stub API; `/runtime` 200, task 202/completed, 15 lifecycle + 1 task + 1 end event, 632.633 ms stream, 967 ms complete, zero real LLM calls.
- `npm ls --depth=0` — exact dependency tree valid; TanStack Query 5.102.3 is the only Stage 19 production dependency addition.
- `python -m unittest discover -s tests` — all 150 backend tests passed in 38.816 seconds after the final frontend changes.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `npm run build` in `apps/web` — strict TypeScript and Vite 8 production build passed; one 336.41 KiB raw/103.85 KiB gzip JavaScript asset and one 13.75 KiB raw/3.48 KiB gzip CSS asset.
- `npx vitest run src/App.test.tsx --reporter=verbose --no-file-parallelism` — 5/5 Stage 18 tests passed in 3.72 seconds.
- Stage 18 axe-core scan — zero automated primary-shell violations; computed color contrast disabled because jsdom cannot measure rendered colors, so this is not certification.
- `npm run check:bundle` — PASS; 102,802 compressed JavaScript bytes ≤256,000.
- Local Vite deep-route request — `GET http://127.0.0.1:4173/runtime` returned HTTP 200.
- npm audit after locked install — 136 packages audited, zero known vulnerabilities reported by npm at installation time.
- `python -m unittest discover -s tests` — all 150 backend regression tests passed in 43.723 seconds after the frontend changes.

- Stage 17 research validation — 28 consecutively numbered references, 38 HTTPS links, required stopping-point text, and all local Markdown links across six changed documents passed static checks.
- Stage 17 frontend implementation boundary check — repository scan found no `apps/`, `frontend/`, `web/`, or `ui/` source, TSX/JSX, `package.json`, Vite config, or TypeScript config.
- `python -m unittest tests.test_acceptance -v` — three Stage 16 acceptance-policy/classification regression tests passed in 0.010 seconds.
- `git diff --check` — exit 0; line-ending notices only.
- Stage 17 changes are documentation-only; the accepted Stage 16 runtime/test evidence remains unchanged.

- `python -m benchmarks.run_stage16_acceptance --output benchmarks/results/stage16-backend-acceptance-20260825T011603Z.json` — exit 0; release candidate true; 14/14 commands and required categories passed.
- Stage 16 complete suite — 150 tests passed in 39.115 seconds.
- Stage 16 targeted controls — eight cancellation/timeout tests passed in 1.060 seconds; six malformed-output/fault tests passed in 4.040 seconds.
- Scheduler — FIFO and priority execution orders matched exactly; resource policy demonstrated all six controlled actions and live `accept`.
- Recovery/trace/observability — killed worker recovered to `completed`, integrity `ok`; replay `matched` with zero deterministic divergences; four tasks/one recovery/55 steps unified.
- Chaos/security — 9/9 expected fault outcomes with recovery 1/1 and 8/9 containment; 14/14 bounded security cases PASS with zero failures and integrity `ok`.
- Deterministic/real API — 16 operations each, zero/one real model calls, both databases integrity `ok`.
- Regression gate — 93.68 tok/s ≥75; TTFT +3.616% ≤50%; RAM 1,343.895≤1,600 MiB; VRAM 1,189≤1,500 MiB; stream 4,589.371≤10,000 ms.
- `python -m unittest tests.test_acceptance -v` — three strict manifest/classification tests passed in 0.017 seconds before the retained full run.

- `python -m unittest tests.test_api -v` — nine Stage 15 real-socket/config tests passed in 10.903 seconds.
- `python -m unittest discover -s tests -v` — 147 tests passed in 40.366 seconds in the final Stage 15 regression run.
- `python -m benchmarks.run_stage15_api` — retained `stage15-api-20260824T205654Z.json`; 16 operations passed from a separate API process with zero direct runtime calls after launch and zero real LLM calls.
- `python -m benchmarks.run_stage15_api --real` — retained `stage15-api-real-20260825T010429Z.json`; 16 operations passed from a separate guarded real-model API process with one Qwen/llama.cpp call.
- Stage 15 retained stream/trace evidence — 15 lifecycle events, terminal task/end events, 16 trace steps with raw payloads omitted, replay integrity valid, and SQLite integrity `ok`.
- Stage 15 retained subsystem evidence — two agents, FIFO scheduler, source-labelled hardware, two registered models, one unified-metrics task, expected isolated model-timeout outcome, and zero retained security failures.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.15.0`, exit 0.
- `python -m runtime --objective "Stage 15 regression smoke task"` — deterministic lifecycle completed with zero real LLM calls, exit 0.
- `python -m runtime.api_cli --help` — documented loopback API options, exit 0.
- Stage 15 config/result/public-import validation — all tracked JSON parsed, retained result passed with integrity `ok`, and Stage 15 factories/API builder imported, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 138 tests passed in 29.058 seconds in the final Stage 14 regression run.
- Stage 14 focused suite — 10 tests passed for strict config, input/payload/secret/output limits, prompt encoding, path allowlists, global tool ceiling, subprocess/process policy, guarded runtime composition, and the complete redacted report.
- `python -m benchmarks.run_stage14_security` — retained `stage14-security-20260824T203349Z.json`; 14/14 PASS, zero FAIL, zero real LLM calls, integrity `ok`, exit 0.
- Stage 14 retained runtime evidence — five tasks, one completion, three `security_blocked`, one `tool_failed`, one stub model call, three tool calls, five trace runs, 55 steps, and 6.242 ms durable collection.
- Stage 14 adversarial suite duration — 2,181.687 ms across the 14 bounded cases.
- Real Stage 14 agent/report — Qwen2.5 1.5B/`performance`; one completed task/model call/route, one prompt-protection event, zero faults, and 19 trace steps; 3,370.565 ms inference, 2,760.402 ms TTFT, 105.39 tok/s, 1,343.949 MiB RAM, and 1,189 MiB VRAM.
- `python -m compileall -q runtime benchmarks tests` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.14.0`, exit 0.
- `python -m runtime --objective "Stage 14 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- Stage 14 retained JSON parsed successfully, contained zero FAIL cases, and did not retain the adversarial fake secret, exit 0.
- Public API import check exposed `build_stage14_runtime` and `security_policy_denied`, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 128 tests passed in 28.987 seconds in the Stage 13 regression run.
- Stage 13 focused suite — 11 tests passed for strict config, explicit arming refusal, inert factory behavior, exact model/tool failure states, count bounds, injection metrics, database-gap reproduction, real factory composition, machine JSON, and killed-process recovery.
- `python -m benchmarks.run_stage13_chaos` — retained `stage13-chaos-20260824T193424Z.json`; 9/9 expected outcomes, 8/9 contained, recovery 1/1, zero real LLM calls, integrity `ok`, exit 0.
- Stage 13 retained baselines — deterministic inference 614.179 ms and read-only tool 562.478 ms; scenario added-latency P50 -71.797 ms/P95 611.597 ms; crash plus recovery 1,648.444 ms.
- Stage 13 observability — 11 tasks, 9 injections, 7 failures, 1 recovery, 11 trace runs, 140 steps, and 9.457 ms durable collection.
- Real Stage 13 agent/report — Qwen2.5 1.5B/`performance`; one completed task/model call/route, 18 trace steps, and zero injected faults; 2,410.179 ms inference, 1,693.755 ms TTFT, 102.59 tok/s, 1,343.566 MiB RAM, and 1,185 MiB VRAM.
- `python -m compileall -q runtime benchmarks tests` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.13.0`, exit 0.
- `python -m runtime --objective "Stage 13 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 117 tests passed in 19.649 seconds in the final Stage 12 gate run.
- Stage 12 focused suite — 9 tests passed for config/limit validation, exact P50/P95 aggregation, absent-value truthfulness, unified activity/failure/recovery/trace reporting, time windows, bounded drill-down, live evidence, real factory composition, and read-only machine-readable reporting.
- `python -m benchmarks.run_stage12_observability` — retained `stage12-observability-20260824T163054Z.json`; expected four-task mix and all totals matched, live hardware present, exit 0.
- Stage 12 retained live report — 1,504.908 ms collection, of which 1,498.907 ms was the live hardware profile; the same durable-only database report collected in 6.543 ms.
- Real Stage 12 agent/report — Qwen2.5 1.5B/`performance`; one task/model call/route and 18 trace steps; 2,927.102 ms inference, 2,238.325 ms TTFT, 96.16 tok/s, 1,343.703 MiB RAM, 1,189 MiB VRAM; query after restart matched every value.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.12.0`, exit 0.
- `python -m runtime --objective "Stage 12 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.

- `python -m unittest discover -s tests` — 108 tests passed in 13.895 seconds in the final Stage 11 gate run.
- Persistence plus Stage 11 focused suites — 20 tests passed; 9 specifically cover v1-to-v2 migration, structured chains, model hashes, bounded replay/no new inference, tamper detection, same/different-run comparison, tool-side-effect skipping, restart loading/factory composition, and CLI demonstration.
- `python -m benchmarks.run_stage11_trace_replay` — retained `stage11-trace-replay-20260824T143744Z.json`; two 15-step runs, replay `matched`, 10 deterministic matches, zero divergences, integrity `ok`, exit 0.
- Real Stage 11 agent — Qwen2.5 1.5B/`performance`; 2,865.074 ms total, 1,989.471 ms TTFT, 94.53 tok/s, 1,345.855 MiB RAM, 1,189 MiB VRAM; completed 18-step trace.
- Real trace inspect/replay — run `af0707f0-6133-4600-bd94-b26896879526`; 11 deterministic, 3 nondeterministic, 4 observational steps; reconstructed `completed`, 11 matches/7 observed-only, chain/SQLite integrity `ok`, exit 0.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.11.0`, exit 0.
- `python -m runtime --objective "Stage 11 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests` — 99 tests passed in 6.524 seconds in the final Stage 10 gate run.
- Stage 10 focused suite — 11 tests passed for schema version/idempotency, newer-schema rejection, illegal-transition rollback, agent conflict, durable record families, tool persistence, restart reconstruction, safe recovery, terminal/in-flight refusal, factory composition, and killed-process CLI recovery.
- `python -m runtime.recovery_cli` — worker process terminated with exit code 1 at durable `planning/recovery_ready`; restarted task completed through `recovering`; SQLite integrity `ok`, exit 0.
- `python -m benchmarks.run_stage10_recovery` — retained `stage10-recovery-20260824T131728Z.json`, final state `completed`, integrity `ok`, exit 0.
- Real Stage 10 agent — Qwen2.5 1.5B/`performance`; 2,891.000 ms task elapsed, 2,125.300 ms backend total, 1,420.839 ms TTFT, 106.76 tok/s, 1,343.590 MiB RAM, 1,189 MiB VRAM; 1 task/output, 5 transitions/checkpoints, 21 events, and 17 steps persisted.
- Real restart inspection — reconstructed task `3626f112-5c0c-4651-8eaf-68bdcddfb20a` as `completed` with `created -> planning -> executing -> validating -> completed`; integrity `ok`; model was not started.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.10.0`, exit 0.
- `python -m runtime --objective "Stage 10 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 88 tests passed in 2.898 seconds in the final Stage 9 gate run.
- Stage 9 focused suite — 9 tests passed for registry validation/availability, different workload routes, explained rejection, context overflow, token/time propagation, zero-call blocking, VRAM-budget profile fallback, factory composition, and CLI output.
- `python -m runtime.routing_cli` — live availability/routes, controlled two-model route split, seven-token cap, and zero-call rejection matched policy; exit 0.
- `python -m benchmarks.run_stage9_routing` — retained `stage9-routing-20260824T124057Z.json`; interactive explanation selected optional compact and standard risk selected installed 1.5B; exit 0.
- Real Stage 9 interactive agent — installed Qwen2.5 1.5B, `performance`, one-call/64-token budget, 32 generated runs, 2,391.000 ms task elapsed, 2,142.737 ms backend total, 1,445.427 ms TTFT, 106.54 tok/s, 1,343.715 MiB RAM, 1,189 MiB VRAM.
- Real Stage 9 background agent — installed Qwen2.5 1.5B, `balanced`, one-call/32-token budget, 25 generated runs, 5,031.000 ms task elapsed, 4,795.147 ms backend total, 1,469.083 ms TTFT, 48.83 tok/s, 1,351.633 MiB RAM, 909 MiB VRAM.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.9.0`, exit 0.
- `python -m runtime --objective "Stage 9 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 79 tests passed in 2.699 seconds in the final Stage 8 gate run.
- Stage 8 focused tests — profile/catalog validation, workload ordering, one-snapshot selection, pressure fallback, missing GPU/RAM, exact native flags, applied metadata, runtime ordering/blocking, CLI, and composition passed.
- `python -m runtime.adaptive_cli` — live standard/interactive selected performance, live background selected balanced; controlled pressure/missing-GPU/missing-RAM behavior matched policy, exit 0.
- `python -m benchmarks.run_stage8_profiles --runs-per-profile 1` — two four-profile runs completed; exploratory `...T121616Z.json` exposed the zero-layer CUDA allocation and final `...T122355Z.json` verified explicit device isolation.
- Stage 8 final profile comparison — performance 100.92 tok/s and 1,189 MiB VRAM; balanced 54.97 tok/s and 909 MiB; constrained 40.41 tok/s and 527 MiB; CPU-safe 27.06 tok/s and 0 MiB.
- Stage 8 failed/kept experiment — zero GPU layers alone still used 311 MiB VRAM; explicit `--device none` reduced the repeated CPU-safe delta to 0 MiB but increased peak host RAM to 1,796.082 MiB and total time to 3,581.382 ms.
- Stage 8 estimator comparison — balanced/constrained VRAM was underpredicted by 23.774/160.110 MiB and CPU-safe host RAM by 375.172 MiB; configured 512/2,048 MiB reserves covered these observed misses, but the extrapolated estimator is not uniformly conservative.
- Stage 8 real standard agent — performance/`ACCEPT`; 2,035.135 ms total, 1,322.844 ms TTFT, 104.46 tok/s, 1,343.508 MiB RAM, 1,189 MiB VRAM, 0.1423 ms queue wait.
- Stage 8 real background agent — balanced/`ACCEPT`; 2,070.558 ms total, 1,317.198 ms TTFT, 69.04 tok/s, 1,351.746 MiB RAM, 909 MiB VRAM, 0.1215 ms queue wait.
- Stage 8 package dry run — would install `local-ai-systems-lab-0.8.0`, exit 0.
- `python -m compileall -q runtime tests benchmarks` and `git diff --check` — exit 0; line-ending notices only.
- `python -m runtime --objective "Stage 8 regression smoke task"` — deterministic stub lifecycle remained intact, exit 0.

- `pwsh -NoProfile -File .\scripts\setup_stage2.ps1` — hashes, llama.cpp version, and CUDA device verified; idempotent rerun passed.
- `python -m unittest discover -s tests -v` — 66 tests passed in 2.091 seconds in the final Stage 7 gate run.
- Stage 7 tests — actual model-file sizing, active/profile mismatch rejection, source-aware profiler parsing, unavailable RAM rejection, estimator/measured comparison, all six policy actions, pre-scheduler event order, accepted execution, and blocked backend non-invocation passed.
- `python -m runtime.hardware_cli` — live hardware/pressure report, `ACCEPT`, calibration comparison, and all six labeled controlled scenarios, exit 0.
- Stage 7 live profile — 72.267 ms; 16,618.473 MiB available RAM; 3,962 MiB free VRAM; `ACCEPT`.
- Stage 7 real admitted Qwen run — admission preceded scheduler submission; 0.2384 ms queue wait, 1,990.603 ms scheduled execution, 1,898.729 ms backend total, 1,332.861 ms TTFT, 111.59 tokens/second, 1,339.113 MiB peak RAM, and 1,219 MiB VRAM delta.
- Scheduler tests — FIFO/priority ordering, stable workload priority, starvation promotion, queued cancellation, busy-worker queue timeout, active timeout signaling, two-worker bounds, runtime result metrics, and terminal-state mapping passed.
- `python -m runtime.scheduler_cli` — same queued submission order produced the expected distinct FIFO and priority execution orders, exit 0.
- Stage 6 controlled priority run — peak queue depth 3; queue-wait P50 0.1344 ms and P95 0.6520 ms.
- Stage 6 controlled FIFO run — queue-wait P50 0.3727 ms and P95 0.7256 ms.
- Stage 6 real scheduled Qwen run — completed with 0.1786 ms queue wait and 1,988.50 ms scheduled execution boundary.
- Stage 6 real inference — 1,898.38 ms backend total, 1,324.55 ms TTFT, 113.77 tokens/second, 1,339.23 MiB peak RAM, and 1,219 MiB VRAM delta.
- Tool tests — permitted result/history, exact-grant denial, path escape, strict types, registry duplicate/missing, timeout signal, external cancellation, invalid result, and cancelled terminal state passed.
- `python -m runtime.tool_cli --demo` — permitted request completed, expected unauthorized request returned `tool_permission_denied`, and command exited 0.
- Stage 5 permitted read — 2.9874 ms tool-handler boundary; `created -> planning -> waiting_for_tool -> validating -> completed`; no inference call.
- Stage 5 denied read — `created -> planning -> security_blocked`; handler was not invoked.
- State-machine tests — deterministic success, illegal jump details, every failure terminal, terminal non-reentry, tool-wait return path, and typed runtime failure mapping passed.
- Native failure-classification test — OOM, context overflow, and generic llama.cpp failures map to distinct typed errors.
- `python -m runtime.agent_cli --agent technical-explainer` — real Qwen execution exposed `created -> planning -> executing -> validating -> completed` with ordered reasons/timestamps.
- Stage 4 real run — 1,825.54 ms total, 1,281.54 ms TTFT, 113.37 tokens/second, 1,339.04 MiB peak RAM, 1,219 MiB VRAM delta.
- `python -m benchmarks.run_stage2_baseline --runs-per-prompt 1` — retained five-run real inference baseline passed.
- Real `--cancel-after-ms 1800` verification — structured cancellation, exit code 130, and GPU memory release passed during Stage 2.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.6.0`, exit 0.
- Stage 7 package dry run — would install `local-ai-systems-lab-0.7.0`, exit 0.
- `python -m runtime --objective "Stage 4 regression smoke task"` — four-event deterministic stub lifecycle remained intact, exit 0.
- `python -m runtime --objective "Stage 7 regression smoke task"` — deterministic stub lifecycle remained intact, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

## Known Problems

- Stage 26 acceptance is scoped to a single-user loopback portfolio release; the standard-library API and Vite preview are not a production serving stack.
- Completed inference results are normalized after restart, while persisted tool-only tasks retain a distinct durable output envelope; a generic task explorer needs a versioned discriminated result union.
- Agent Browser is an exact development-only dependency for product verification; it is absent from the production bundle and does not replace human accessibility or visual review.
- The Stage 26 browser uses a deterministic stub for repeatability; the mandatory inherited gate separately proves one real local-model call, not semantic output quality.
- Python 3.11 on Windows exposes an open-handle cleanup incompatibility in the deliberately injected SQLite failure path; Python 3.10 is the verified project runtime.
- Runtime, Agents, Scheduler, Traces, Hardware, Metrics, Chaos, and Security are real workbench routes; Models, Tasks, and Settings retain honest endpoint placeholders until their approved scopes.
- The backend exposes no bounded task-list endpoint; the UI cannot claim or render a complete task history.
- A refreshed terminal task remains inspectable through durable state history and its safe trace, but its transient SSE rail is not reconstructed.
- Aborting concurrent polling during Windows HMR/process teardown can print noisy development-server `ConnectionAbortedError` tracebacks; successful responses and shutdown remain unaffected.
- The 250 KiB compressed shell budget and 10,000-step/100-row DOM bound pass, but real-browser INP, long tasks, heap growth, high-volume stream-update cost, and polling contention remain unmeasured.
- CPU utilization and continuous hardware history are unavailable; the accepted profiler supplies topology/current memory/GPU evidence and metrics supplies bounded task history.
- Automated accessibility evidence is not WCAG conformance; jsdom did not compute color contrast and no NVDA/forced-color/400%-zoom/browser matrix was run.
- The shell is dark-first; no light theme has been designed or validated.
- Native routing intentionally handles shallow top-level routes plus validated `?task=` and optional `?step=` parameters; deeper nested resources may justify a maintained router.
- No screenshot asset or browser visual-regression suite exists; Stage 23 validation covers compilation, DOM behavior, eight automated route accessibility scans, bounded selections, propagation/recovery, attack/blocked-action evidence, real API smoke, and bundle size.
- Confirmed chaos/security requests run synchronously; repeated submissions are distinct experiments and there is no idempotency key or campaign queue.
- Security reports are latest-by-UTC filename; concurrent retained history has no indexed pagination contract.

- Backend acceptance is scoped and overall maturity is `PARTIAL`; release-candidate status must not be presented as production or multi-user readiness.
- The terminal-state/output atomicity gap remains the principal accepted reliability limitation and keeps persistence/recovery plus fault injection `PARTIAL`.
- Only one real model backend exists and semantic output evaluation remains deferred, so model routing/evaluation is `PARTIAL`.

- The standard-library HTTP server is a loopback development adapter, not an internet-facing production server; TLS, authentication, multi-user authorization, proxy trust, and identity-based rate limits are absent.
- HTTP handler/SSE connection count is not globally capped; body, task, scheduler, inference, and stream limits bound the demonstrated path but do not isolate hostile clients.
- API task records and SSE cursors are process-local. Completed durable tasks can be inspected after restart, but arbitrary active-task continuation is not promised beyond the explicit safe checkpoint contract.
- Completed API task records are retained in process memory until shutdown; a long-lived service needs a measured eviction/pagination policy before unbounded task volume.
- Task inspection returns validated objectives, inputs, and outputs to the local caller; system prompts and trace payloads are omitted, but data retention/deletion/export policy remains incomplete.

- Prompt separation and system instructions do not eliminate direct or indirect prompt injection; deterministic least privilege limits impact, but model behavior remains nondeterministic.
- Network denial is enforced at the application capability layer, not by a firewall, container, VM, or network namespace.
- Secret protection uses finite patterns and sensitive key names, so false positives and false negatives remain possible.
- Validated objectives and outputs remain in the ignored local SQLite database; encryption at rest, retention automation, and secure deletion are not implemented.
- The subprocess policy validates the pinned inference contract; the native executable is hash-pinned but not OS-sandboxed.
- The infinite-loop adversarial case verifies cooperative cancellation only. Python cannot forcibly terminate a hostile handler thread, so untrusted handlers remain prohibited.
- Structural/secret output validation does not prove semantic correctness, factuality, safety, or specialized-role compliance.
- The 14/14 result is bounded test evidence, not penetration testing, certification, or a claim that the system is secure.

- Automatic recovery resumes only from a pre-invocation planning checkpoint; native token generation and arbitrary tool/model execution cannot be resumed.
- Scheduler queue/worker internals are not reconstructed; a safe recovered task is resubmitted through current policy, routing, admission, and scheduling.
- A second crash after entering `RECOVERING` is classified unsafe rather than automatically retried.
- Terminal state and output are committed in adjacent transactions; Stage 13 reproduced the gap with a task left `completed` and no output after `database_operation_failed`. It requires manual repair rather than unsafe duplication.
- SQLite is local single-host persistence, not distributed coordination or a multi-process cluster database.
- Database backup/restore, compaction/retention, encryption at rest, and forward migration beyond schema v2 are not implemented.
- Trace hashes provide tamper evidence but are not signed/authenticated against an attacker able to rewrite both payloads and hashes.
- Trace payloads can retain validated local objectives, tool arguments, and outputs; Stage 14 redacts lifecycle/metric evidence, but database retention/export policy remains incomplete.
- Replay reconstructs deterministic execution evidence; it does not rerun llama.cpp token generation, reproduce hardware timing, or repeat tool side effects.
- Pre-Stage-11 data migrates safely but is not backfilled into fabricated historical trace runs.
- Cross-run comparison is structural/semantic hash comparison, not model-output quality evaluation.
- Eight retained faults are controlled protocol simulations; only the agent-crash scenario terminates an actual OS process.
- Fault activation state is process-local; there is no distributed campaign coordinator or persistent chaos schedule.
- Negative added latency means fail-fast relative to successful baseline completion, not faster useful work.

- Only one real GGUF/backend is installed and configured; real multi-model switching is not claimed.
- The compact registry entry is unavailable and unbenchmarked; its controlled route uses simulated availability with the stub-compatible boundary only.
- Capability labels and quality ranks are static policy metadata; output validation still cannot prove semantic correctness.
- Budget memory enforcement uses preflight estimates; observed peak measurements are reported afterward and estimator misses remain possible.
- The router and adaptive controller take separate live hardware snapshots, so pressure can change between model selection and exact profile admission; the later admission decision remains authoritative.
- Routing decisions, budgets, and usage records now appear in the Stage 12 unified task/report view; semantic output evaluation remains future work.

- Queue state and request handles remain process-local; durable lifecycle/metric events survive, but the scheduler queue itself is not reconstructed.
- The public `AgentRuntime.run()` call waits synchronously even though scheduler requests are internally queued.
- Python cannot forcibly stop a non-cooperative scheduled operation thread; logical timeout/cancellation returns and signals the token.
- Priority defaults and aging/starvation thresholds are transparent baselines, not workload-tuned optimal values.
- Adaptation is limited to four discrete profiles; continuous recommendation-to-parameter conversion is intentionally absent.
- The scheduler does not preempt an operation that has already started.
- Tool timeout returns control and signals cancellation, but Python cannot forcibly stop a non-cooperative handler thread; only vetted handlers are permitted.
- The two safe tools provide application-level path containment, not process or OS sandboxing.
- Tool definitions and grants remain static in code; tool invocation requests/results/errors are durable.
- Only read-only project text tools exist; writes, subprocesses, network access, and arbitrary binary reads remain prohibited.
- Output validation rejects blank, oversized, control-character, and detected secret-like text but still does not detect semantic role/factual failures.
- Transition histories, agent snapshots, lifecycle events, metrics, checkpoints, traces, and replay reports are durable in SQLite schema v2.
- An intermediate real prompt experiment completed but inverted privacy wording and drifted into training; bounded role prompts corrected the final run, but no output validator exists.
- The real backend reloads the model for every request, making median cold TTFT about 1.69 seconds.
- The backend accepts only one active inference per instance; the real scheduler is deliberately configured with one worker.
- VRAM is sampled at 200 ms via total-device `nvidia-smi` data and can include unrelated GPU use.
- The five-prompt, single-iteration sample is acceptance evidence, not a statistically strong performance claim.
- A 64-token cap truncated some longer answers; one JSON-only prompt included Markdown fences, so no broad quality claim is made.
- Routing is explainable and dynamic within registered models, while Stage 14 security remains application-level policy rather than an OS sandbox.
- Observability is pull-based and local; there is no remote collector, alerting pipeline, or public API, and the frontend remains a local pull-based projection.
- Live scheduler state belongs to the reporting runtime process; historical scheduler behavior is represented separately by durable event distributions.
- Recent task drill-down uses bounded follow-up queries and is not yet optimized for large databases.
- Physical core count is not accessible through the narrow live profiler and remains explicitly unavailable; the declared eight-core constraint is not relabeled as observed.
- The memory estimator is calibrated against one model/configuration/run. It does not establish accuracy for larger models, quantizations, contexts, or concurrency.
- `nvidia-smi` reports device-wide pressure and can include unrelated GPU allocations.
- `QUEUE` is an advisory admission decision and does not silently enter the execution scheduler; callers must retry so memory is re-profiled.
- Profile measurements contain one run per profile and cannot support strong statistical or universal tuning claims.
- Balanced/constrained profiles change several variables together, so this experiment cannot isolate which flag caused a difference.
- Zero GPU layers alone still initialized 311 MiB VRAM; CPU-safe now also requires `--device none`, which measured 0 MiB but increases host RAM/latency.
- Profile catalog values and workload order are static, model-specific, and not learned from benchmark history.
- The Stage 7 estimator underpredicts some Stage 8 profiles; reserves covered the observed sample, but per-profile recalibration remains necessary.
- No Python dependency lock is necessary while project dependencies remain empty; revisit this when a Python dependency is introduced.
- WMI/CIM hardware queries are access-restricted in the current execution context; the environment checker uses narrower registry/.NET/NVIDIA queries.
- The Windows registry product label reports `Windows 10 Home Single Language` while build/display-version evidence is `26200.9168` / `25H2`; the report preserves the raw evidence rather than inferring a marketing name.
- The installed Hugging Face CLI 0.36.0 lacks newer `hf models info`/dry-run forms; exact Hub revision metadata and the pinned download path were used instead.
- The first benchmark file-path invocation failed to import `runtime`; the benchmark became a package and the documented module invocation passed.

## Performance Baseline

The Stage 2 five-run cold baseline remains: median model load 1,128.28 ms; TTFT 1,686.85 ms; generation 115.81 tokens/second; total 2,572.26 ms; peak child-process RAM 1,339.02 MiB; VRAM delta 1,219 MiB. The final Stage 8 comparison observed performance/balanced/constrained/CPU-safe VRAM deltas of 1,189/909/527/0 MiB. Stage 12 real inference measured 2,927.102 ms total, 2,238.325 ms TTFT, 96.16 tokens/second, 1,343.703 MiB RAM, and 1,189 MiB VRAM. Stage 13 deterministic no-fault baselines were 614.179 ms inference and 562.478 ms tool; injected scenario added latency measured P50 -71.797 ms/P95 611.597 ms, and the actual killed-worker recovery took 1,648.444 ms. Stage 14's deterministic 14-case suite completed in 2,181.687 ms; it is control evidence, not an inference-performance benchmark. The guarded real Stage 14 run measured 3,370.565 ms inference, 2,760.402 ms TTFT, 105.39 tokens/second, 1,343.949 MiB RAM, and 1,189 MiB VRAM. Stage 15's external stub API measured task create 139.048 ms, SSE-to-terminal 583.177 ms, trace replay 47.929 ms, metrics retrieval 88.731 ms, live hardware retrieval 1,298.973 ms, and isolated model-timeout chaos 2,254.988 ms; these are one-run integration timings, not throughput claims. The real external API run measured 2,973.505 ms inference, 2,210.807 ms TTFT, 103.32 tok/s, 1,343.887 MiB RAM, and 1,189 MiB VRAM. Stage 16's retained gate run measured 2,375.729 ms real inference, 1,747.840 ms TTFT, 93.68 tok/s, 1,343.895 MiB RAM, 1,189 MiB VRAM, and 4,589.371 ms end-to-end HTTP/SSE streaming; TTFT was 3.616% above the Stage 2 median and all five configured regression limits passed. Stage 18's shell build is 102,802 gzip JavaScript bytes and 3.48 KiB gzip CSS; the five DOM tests took 3.72 seconds. Stage 19 measures 117,956 gzip JavaScript bytes (+14.7%), 4.66 KiB gzip CSS, seven DOM tests in 4.48 seconds, and a 632.633 ms one-task stub SSE stream/967 ms complete smoke. These are build and one-run local integration measurements; no real-browser interaction timing is claimed. See [the Stage 2 report](docs/benchmarks/stage2-local-inference-baseline.md), [Stage 8 final comparison](benchmarks/results/stage8-profile-comparison-20260824T122355Z.json), [Stage 12 result](benchmarks/results/stage12-observability-20260824T163054Z.json), [Stage 13 result](benchmarks/results/stage13-chaos-20260824T193424Z.json), [Stage 14 result](benchmarks/results/stage14-security-20260824T203349Z.json), [Stage 15 stub result](benchmarks/results/stage15-api-20260824T205654Z.json), [Stage 15 real result](benchmarks/results/stage15-api-real-20260825T010429Z.json), [Stage 16 acceptance result](benchmarks/results/stage16-backend-acceptance-20260825T011603Z.json), and [Stage 19 smoke result](benchmarks/results/stage19-runtime-command-center-20260825T121824Z.json).

Stage 20 adds 121,569 gzip JavaScript bytes (+3.1% from Stage 19), 5.54 KiB gzip CSS, 12 DOM tests in 5.43 seconds, and a 770.484 ms complete task/state/scheduler smoke with five durable transitions and 50.385 ms scheduler execution. See [the Stage 20 smoke result](benchmarks/results/stage20-agent-scheduler-20260825T124614Z.json).

Stage 21 adds a 16-step/692 ms real safe trace, 19.362 ms trace retrieval,
29.216 ms valid replay, and an 841.405 ms complete local smoke. The replay
matched 11 deterministic reducers, observed five nondeterministic/observational
steps, and reported zero divergence, side-effect skips, or integrity failure.
A 10,000-step component fixture verifies only 100 timeline rows render per page;
that focused interaction completed in 2.284 seconds during the final suite.
The Stage 21 build is 124,662 gzip JavaScript bytes (48.7% of the 256,000-byte
gate) and 6,393 gzip CSS bytes; 18 DOM tests took 6.94 seconds.
See [the Stage 21 smoke result](benchmarks/results/stage21-trace-replay-20260825T130714Z.json).

Stage 22 adds a 789.314 ms real hardware profile, 802.412 ms parallel
hardware/model/scheduler plus durable-metrics retrieval, and a 1,610.033 ms
complete smoke. It measured Ryzen 7/16 logical processors/32,097.656 MiB RAM
and RTX 3050/4,096 MiB VRAM, then retained one completed stub task with zero
TTFT/token-rate samples rather than converting missing values to zero. See
[the Stage 22 smoke result](benchmarks/results/stage22-hardware-performance-20260825T133404Z.json).

The Stage 22 build is 127,686 gzip JavaScript bytes (49.9% of the
256,000-byte gate) and 7,365 gzip CSS bytes; 23 DOM tests took 7.95 seconds.

Stage 23 adds a 10.376 ms catalog retrieval, a 4,725.132 ms confirmed three-fault
HTTP run, a 2,594.815 ms confirmed fourteen-case security HTTP run, and a
7,390.419 ms complete local smoke. Chaos produced 3/3 expected outcomes, 2/3
containment with the known persistence gap, 1/1 successful crash recovery,
1,048.260 ms P95 added latency, integrity `ok`, and zero real model calls.
Security produced 14/14 expected defenses, zero failures/model calls, 2,355.228 ms
suite duration, integrity `ok`, and an immediately matching retained result.
See [the Stage 23 smoke result](benchmarks/results/stage23-chaos-security-20260825T143324Z.json).

The Stage 23 build is 130,676 gzip JavaScript bytes (51.0% of the
256,000-byte gate) and 8,333 gzip CSS bytes; 28 DOM tests took 9.75 seconds.

Stage 24 adds a 58.705 ms complete local smoke with six HTTP 200 workbench
routes, 22.357–48.888 ms route retrieval, 24.46 ms median route retrieval, and
26.329 ms health retrieval while the runtime remained running with integrity
`ok`. See [the Stage 24 smoke result](benchmarks/results/stage24-interaction-motion-20260826T155934Z.json).

The Stage 24 build is 149,836 gzip JavaScript bytes (58.5% of the
256,000-byte gate) and 9.36 KiB gzip CSS; 34 DOM tests passed with 12.26 seconds
of test time. The 19,160-byte/14.7% JavaScript increase activates the existing
React Aria overlay/list behavior for command navigation.

Stage 25 adds an 87.819 ms complete local smoke with all twelve HTTP 200
workbench routes, 30.933–56.046 ms route retrieval, 37.401 ms median route
retrieval, and 34.123 ms health retrieval while runtime remained `running` and
integrity `ok`. Nine calculated token pairs pass their 4.5:1 text or 3:1 focus
threshold; the minimum tracked text ratio is 4.81:1. See [the Stage 25 smoke
result](benchmarks/results/stage25-responsive-accessibility-performance-20260826T182119Z.json).

The Stage 25 build is 150,118 gzip JavaScript bytes (58.6% of the
256,000-byte gate) and 9.43 KiB gzip CSS; 38 DOM tests passed with 12.73 seconds
of test time. A 500-event fixture commits one animation frame, retains 200
events, and renders 30 lifecycle rows; the existing 10,000-step fixture renders
100 rows per page. The Vite development route/health timings are one-run local
samples, not field interaction or Core Web Vitals evidence.

Stage 26 retains one complete release-candidate gate. Backend acceptance took
91,410.474 ms and measured one real inference at 1,801.341 ms TTFT, 103.47
tokens/second, 2,408.659 ms total, 1,343.680 MiB peak process RAM, and 1,189 MiB
VRAM delta. Frontend tests took 35,391.660 ms, the build 5,929.256 ms, and the
bundle check 1,565.495 ms. The browser product journey took 65,656.979 ms,
rendered eight routes, and measured 2.5 ms TTFB, 76 ms FCP/LCP, and CLS 0.01;
INP was unavailable. The read-only tool completed in 2.531 ms. JavaScript is
150,997 gzip bytes (59.0% of the 256,000-byte gate). These are one-run local lab
measurements, not field performance. See [the Stage 26 acceptance result](benchmarks/results/stage26-product-acceptance-20260827T101438Z.json).

## Backend Acceptance Status

PASS WITH TRACKED LIMITATIONS. All mandatory backend and product categories pass;
release candidate true; overall maturity `PARTIAL`. Stage 26 adds only bounded,
server-catalogued read-only tool execution and isolated verification; it does not
broaden normal runtime authority or remote exposure.

## Frontend Research Status

COMPLETE. The 2026-08-25 research contains 28 references and its Systems
Cartography recommendation is now encoded in the Stage 18 design system and
local application shell plus the Stage 19 Runtime Command Center and Stage 20
Agent & Scheduler Visualization, Stage 21 Trace Explorer & Replay Debugger, and
Stage 22 Hardware & Performance Lab plus Stage 23 Chaos & Security Lab.
Stage 24 implements its native interaction recommendation without adding a motion runtime.
Stage 25 verifies and hardens that recommendation without adding a dependency.
Stage 26 verifies the complete implemented product and adds only an exact
development-time browser driver plus the server-catalogued Safe Tool Probe.

## Next Step

Stage 27 — Product Demonstration & Portfolio Packaging

## Later Backlog

Stage 27 remains intentionally deferred and requires explicit approval.
