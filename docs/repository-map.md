# Repository Map

## Reconstruction result

At the start of Stage 0, commit `67ef780` contained one tracked file:
`README.md` with only the project heading. The `main` worktree was clean and
matched `origin/main`. There were no source directories, tests, configuration
files, dependency manifests, architecture documents, or TODO/FIXME markers.

## Structure after Stage 27

```text
Local-AI-System-Lab/
├── .gitignore
├── README.md                          # Entry point, demo, and approval status
├── PROJECT_STATE.md                   # Repository source of truth
├── setup_and_run.bat                 # Windows setup plus backend-first local launcher
├── pyproject.toml                     # Python >=3.10 package metadata and CLIs
├── apps/
│   └── web/
│       ├── package.json                # Local React/Vite scripts and bounded dependencies
│       ├── package-lock.json           # Exact frontend dependency graph
│       ├── index.html                  # Local application document and metadata
│       ├── vite.config.ts              # Validated loopback dev/preview server and /v1 proxy
│       ├── vitest.config.ts            # jsdom/component test environment
│       ├── tsconfig*.json               # Strict browser/build TypeScript projects
│       ├── scripts/check-bundle.mjs    # 250 KiB compressed shell gate
│       ├── scripts/stage19-smoke.mjs   # Real Vite-proxy/API/SSE evidence run
│       ├── scripts/stage25-smoke.mjs   # Routes/contrast/reflow/stream/bundle smoke
│       ├── scripts/stage26-browser.mjs # Isolated full-story and restart browser verification
│       └── src/
│           ├── App.tsx                 # Thin application entry component
│           ├── App.test.tsx            # Runtime/task/SSE/navigation/preference/axe tests
│           ├── main.tsx                # React root and global styles
│           ├── api/                     # Typed envelope client and real payload contracts
│           ├── components/             # Shell plus runtime/task/tool/evidence surfaces
│           ├── hooks/                   # Density, route-task, media, and SSE ownership
│           ├── navigation/             # Route definitions and History adapter
│           ├── query/                   # TanStack Query provider, keys, polling, mutations
│           ├── styles/                 # Systems Cartography tokens and global CSS
│           └── test/                   # DOM environment and transport fixtures
├── configs/
│   ├── inference-baseline.json        # Pinned backend/model/runtime settings
│   ├── admission-baseline.json        # Model metadata, estimator, reserves, calibration
│   ├── inference-profiles.json        # Typed adaptive resource-profile catalog
│   ├── model-registry.json            # Model availability and workload budgets
│   ├── persistence.json               # SQLite path, timeout, journal, durability mode
│   ├── observability.json             # Report window, drill-down limits, live-probe policy
│   ├── chaos.json                     # Disabled-by-default bounded fault scenarios
│   ├── security.json                  # Strict local security ceilings and allowlists
│   ├── api.json                       # Loopback bind and API/task/stream/chaos bounds
│   ├── acceptance.json                # Stage 16 scope, evidence counts, regression limits
│   └── product-acceptance.json        # Stage 26 route/failure/browser/tool/bundle policy
├── benchmarks/
│   ├── __init__.py
│   ├── run_stage2_baseline.py         # Reproducible benchmark runner
│   ├── run_stage8_profiles.py         # Same-workload resource-profile runner
│   ├── run_stage9_routing.py          # Controlled explained route comparison
│   ├── run_stage10_recovery.py        # Killed-process recovery evidence runner
│   ├── run_stage11_trace_replay.py    # Trace/replay/comparison evidence runner
│   ├── run_stage12_observability.py   # Unified telemetry evidence runner
│   ├── run_stage13_chaos.py           # Complete controlled chaos runner
│   ├── run_stage14_security.py        # Complete adversarial evidence runner
│   ├── run_stage15_api.py             # Separate-process external API evidence runner
│   ├── run_stage16_acceptance.py      # Complete classified backend gate
│   ├── prompts/stage2-baseline.json   # Five-prompt tracked workload
│   ├── results/stage2-baseline-20260823T180550Z.json
│   ├── results/stage8-profile-comparison-20260824T121616Z.json # Exploratory zero-layer run
│   ├── results/stage8-profile-comparison-20260824T122355Z.json # Final explicit-device run
│   ├── results/stage9-routing-20260824T124057Z.json # Controlled route result
│   ├── results/stage10-recovery-20260824T131728Z.json # Retained restart result
│   ├── results/stage11-trace-replay-20260824T143744Z.json # Retained replay result
│   ├── results/stage12-observability-20260824T163054Z.json # Retained telemetry result
│   ├── results/stage13-chaos-20260824T193424Z.json # Retained fault/recovery result
│   ├── results/stage14-security-20260824T203349Z.json # Retained PASS/FAIL result
│   ├── results/stage15-api-20260824T205654Z.json # Retained deterministic HTTP/SSE result
│   ├── results/stage15-api-real-20260825T010429Z.json # Retained real Qwen API result
│   ├── results/stage16-backend-acceptance-20260825T011603Z.json # Retained gate result
│   ├── results/stage19-runtime-command-center-20260825T121824Z.json # Retained frontend/API smoke
│   ├── results/stage20-agent-scheduler-20260825T124614Z.json # Retained state/scheduler smoke
│   ├── results/stage21-trace-replay-20260825T130714Z.json # Retained trace/replay smoke
│   ├── results/stage22-hardware-performance-20260825T133404Z.json # Retained performance smoke
│   ├── results/stage23-chaos-security-20260825T143324Z.json # Retained experiment UI smoke
│   ├── results/stage24-interaction-motion-20260826T155934Z.json # Retained interaction contract smoke
│   └── results/stage25-responsive-accessibility-performance-20260826T182119Z.json # Retained hardening smoke
├── docs/
│   ├── architecture.md                # Implemented/deferred component boundaries
│   ├── development.md                 # Reproducible run/test/check commands
│   ├── environment.md                 # Measured workstation/tool baseline
│   ├── frontend-research.md            # Stage 17 evidence and frontend recommendation
│   ├── frontend-design-system.md       # Stage 18 executable language and UI architecture
│   ├── repository-map.md              # This inventory
│   ├── risks.md                       # Evidence-based risk register
│   ├── backend-acceptance-report.md   # Human release-candidate decision
│   ├── benchmarks/
│   │   └── stage2-local-inference-baseline.md
│   ├── stages/
│   │   ├── stage3-agent-runtime-mvp.md
│   │   ├── stage4-explicit-state-machine.md
│   │   ├── stage5-tool-runtime-permissions.md
│   │   ├── stage6-request-scheduler.md
│   │   ├── stage7-hardware-profiler-admission.md
│   │   ├── stage8-adaptive-inference-controller.md
│   │   ├── stage9-model-registry-router-budgets.md
│   │   ├── stage10-persistence-checkpoints-recovery.md
│   │   ├── stage11-execution-trace-deterministic-replay.md
│   │   ├── stage12-observability-metrics-backend.md
│   │   ├── stage13-fault-injection-chaos-framework.md
│   │   ├── stage14-security-adversarial-testing.md
│   │   ├── stage15-backend-api-full-runtime-integration.md
│   │   ├── stage16-backend-verification-acceptance-gate.md
│   │   ├── stage18-design-system-ui-architecture.md
│   │   ├── stage19-runtime-command-center.md
│   │   ├── stage20-agent-scheduler-visualization.md
│   │   ├── stage21-trace-explorer-replay-debugger.md
│   │   ├── stage22-hardware-performance-lab-ui.md
│   │   ├── stage23-chaos-security-lab-ui.md
│   │   ├── stage24-advanced-interaction-motion-polish.md
│   │   └── stage25-responsive-accessibility-performance-pass.md
│   └── adr/
│       ├── README.md                  # ADR process and index
│       ├── 0001-stage-gated-modular-backend-first.md
│       ├── 0002-typed-protocols-and-stdlib-skeleton.md
│       ├── 0003-pinned-llama-cpp-qwen-baseline.md
│       ├── 0004-registered-agent-runtime-and-lifecycle-events.md
│       ├── 0005-validated-execution-state-machine.md
│       ├── 0006-default-deny-bounded-tool-runtime.md
│       ├── 0007-bounded-aged-priority-scheduler.md
│       ├── 0008-conservative-pre-scheduler-memory-admission.md
│       ├── 0009-discrete-re-admitted-inference-profiles.md
│       ├── 0010-explainable-availability-gated-model-routing.md
│       ├── 0011-sqlite-checkpoints-and-pre-invocation-recovery.md
│       ├── 0012-hash-chained-traces-and-bounded-replay.md
│       ├── 0013-sqlite-windowed-observability-snapshots.md
│       ├── 0014-bounded-protocol-fault-injection.md
│       ├── 0015-deterministic-security-boundaries.md
│       ├── 0016-loopback-stdlib-http-json-sse-api.md
│       ├── 0017-scoped-evidence-based-backend-acceptance.md
│       ├── 0018-systems-cartography-web-shell.md
│       ├── 0019-real-loopback-query-and-sse-client.md
│       ├── 0020-task-scoped-agent-scheduler-projections.md
│       ├── 0021-redacted-trace-projection-and-explicit-replay.md
│       ├── 0022-source-labelled-performance-projection.md
│       ├── 0023-server-catalogued-confirmed-experiment-ui.md
│       ├── 0024-native-progressive-interaction-layer.md
│       ├── 0025-container-aware-accessible-bounded-rendering.md
│       └── template.md
├── runtime/
│   ├── __init__.py                    # Public runtime API through Stage 15
│   ├── __main__.py                    # `python -m runtime` entry point
│   ├── agent_cli.py                   # Real specialized-agent demonstration
│   ├── agents.py                      # Two registered Stage 3 role definitions
│   ├── cli.py                         # JSON lifecycle demonstration
│   ├── config.py                      # Validated typed configuration
│   ├── cancellation.py                # Thread-safe cancellation token
│   ├── engine.py                      # AgentRuntime orchestration
│   ├── errors.py                      # Structured error hierarchy
│   ├── factory.py                     # Dependency composition root
│   ├── in_memory.py                   # Deterministic stub implementations
│   ├── interfaces.py                  # Replaceable component protocols
│   ├── inference_cli.py               # Real inference/stream/cancel CLI
│   ├── hardware_cli.py                # Live profile/admission report and policy demo
│   ├── adaptive_cli.py                # Live/controlled resource-profile selection
│   ├── routing_cli.py                 # Registry, routes, and budget controls
│   ├── recovery_cli.py                # Killed-worker restart/recovery demo
│   ├── trace_cli.py                   # Trace inspect/replay/compare/demo CLI
│   ├── observability_cli.py           # Live/recent JSON telemetry CLI
│   ├── chaos_cli.py                   # Explicitly armed fault/recovery suite
│   ├── security_cli.py                # Adversarial PASS/FAIL suite
│   ├── api_cli.py                     # Loopback full-runtime HTTP/SSE service
│   ├── api/
│   │   ├── config.py                  # Strict loopback and request/task/stream bounds
│   │   ├── models.py                  # External task record/status/result schemas
│   │   ├── manager.py                 # Bounded task ownership and cancellation
│   │   ├── service.py                 # Integrated transport-independent operations
│   │   ├── openapi.py                 # OpenAPI 3.1 route document
│   │   └── server.py                  # HTTP/JSON and SSE adapter
│   ├── models.py                      # Typed domain/component data
│   ├── state_machine.py               # Legal graph and ordered histories
│   ├── scheduler_cli.py               # FIFO/priority ordering comparison
│   ├── scheduler/
│   │   ├── models.py                  # Options, statuses, results, queue metrics
│   │   └── queued.py                  # Bounded FIFO/priority worker queue
│   ├── hardware/
│   │   ├── models.py                  # Evidence, estimate, and decision schemas
│   │   ├── profiler.py                # Source-aware live host/device snapshot
│   │   ├── config.py                  # File-backed model/estimator configuration
│   │   ├── estimator.py               # Transparent calibrated memory formula
│   │   └── admission.py               # Six-action policy and runtime gate
│   ├── adaptive/
│   │   ├── models.py                  # Attempt and selection evidence
│   │   ├── config.py                  # Validated profile catalog loader
│   │   └── controller.py              # Workload ordering and candidate re-admission
│   ├── routing/
│   │   ├── models.py                  # Registry, route, budget, and usage evidence
│   │   ├── config.py                  # Registry and workload-budget loader
│   │   └── router.py                  # Availability filtering and explained scoring
│   ├── persistence/
│   │   ├── config.py                  # Validated SQLite configuration
│   │   ├── models.py                  # Recovery disposition/candidate evidence
│   │   ├── adapters.py                # Narrow protocol adapters over shared storage
│   │   └── sqlite_store.py            # Schema, transactions, records, recovery ledger
│   ├── tracing/
│   │   ├── models.py                  # Run/step/replay/comparison records
│   │   ├── hashing.py                 # Canonical/semantic hashes and classification
│   │   ├── replay.py                  # Integrity replay and cross-run comparison
│   │   └── store.py                   # Narrow SQLite trace adapter
│   ├── observability/
│   │   ├── config.py                  # Validated report-window/limit settings
│   │   ├── models.py                  # Unified report and distribution records
│   │   ├── store.py                   # Narrow SQLite telemetry source
│   │   └── backend.py                 # Aggregation and optional live snapshots
│   ├── faults/
│   │   ├── models.py                  # Scenario, plan, record, and report contracts
│   │   ├── config.py                  # Strict disabled-by-default plan loader
│   │   ├── controller.py              # Count bounds, delay, and injection metrics
│   │   ├── adapters.py                # Inference/tool/persistence decorators
│   │   └── runner.py                  # Expected/actual scenario execution
│   ├── security/
│   │   ├── models.py                  # Per-case and suite evidence contracts
│   │   ├── config.py                  # Strict security configuration loader
│   │   ├── policy.py                  # Input/output/path/tool/network/process controls
│   │   └── runner.py                  # Fourteen adversarial cases
│   ├── tool_cli.py                    # Permitted/denied tool demonstration
│   ├── tools/
│   │   ├── models.py                  # Typed schemas, permissions, requests/results
│   │   ├── registry.py                # Exact-name process-local registry
│   │   ├── policy.py                  # Default-deny agent grant checks
│   │   ├── validation.py              # Strict argument/result validation
│   │   ├── executor.py                # Deadline/cancellation execution boundary
│   │   └── safe_tools.py              # Root-contained read-only tools
│   └── inference/
│       ├── config.py                  # Pinned inference config loader
│       ├── llama_cpp.py               # Native subprocess adapter
│       └── metrics.py                 # Log parser and RAM/VRAM sampler
├── scripts/
│   ├── check_environment.ps1          # Read-only environment inventory
│   └── setup_stage2.ps1               # Pinned artifact installer/verifier
└── tests/
    ├── fixtures/fake_llama.py          # Controllable subprocess test double
    ├── __init__.py
    ├── test_agent_runtime.py           # Registry/run/state/event coverage
    ├── test_adaptive_inference.py      # Profiles, selection, flags, runtime and CLI
    ├── test_cli.py
    ├── test_config_and_errors.py
    ├── test_interfaces.py
    ├── test_inference_metrics.py
    ├── test_hardware_admission.py      # Profile, estimate, policy, and gate coverage
    ├── test_llama_cpp_backend.py
    ├── test_model_routing.py          # Registry, route, budget, CLI, and factory tests
    ├── test_persistence_recovery.py   # Schema, durability, restart, kill/recovery tests
    ├── test_tracing_replay.py         # Migration, chain, tamper, replay, compare, CLI
    ├── test_observability.py          # Windows, aggregates, live evidence, CLI, factory
    ├── test_fault_injection.py        # Arming, faults, gap, reports, killed-process recovery
    ├── test_security.py               # Policy, runtime, redaction, and full-suite coverage
    ├── test_api.py                    # Real-socket JSON/SSE/control/integration coverage
    ├── test_acceptance.py             # Strict policy and classification coverage
    ├── test_runtime.py
    ├── test_scheduler.py               # Ordering, bounds, timeout, cancellation, aging
    ├── test_scheduler_cli.py           # Visible FIFO/priority comparison
    ├── test_state_machine.py           # Legal/illegal/failure transition coverage
    ├── test_tool_cli.py                # Allowed/denied demonstration coverage
    └── test_tool_runtime.py            # Tool policy, validation, bounds, and path tests
```

Ignored `tools/` and `models/` directories contain the verified native binaries
and GGUF file; they are reproducible artifacts, not source. No empty future
directories are added merely to imply implementation.

## Component inventory after Stage 27

| Area | Prior evidence | Current state | Evidence |
| --- | --- | --- | --- |
| Repository | Security result/report, ADR-0015, and 0.14.0 identity | Adds API result/report, ADR-0016, and 0.15.0 identity | README, Stage 15 result, ADR index |
| Runtime | Complete guarded synchronous orchestration | Adds Stage 15 real/stub compositions and bounded asynchronous API ownership without coupling core protocols to HTTP | Factory and API tests |
| Task control | Caller blocks in `AgentRuntime.run()` | External create/inspect/cancel plus durable completed-task inspection after API restart | Task/SSE/cancellation/restart tests |
| Inspection | Separate CLIs and Python component calls | Safe HTTP views for agents, scheduler, hardware, models/budgets, metrics, and traces/replay | External API result |
| Reliability/security | Explicit local CLIs | Confirmed isolated chaos and retained security-result endpoints; serving runtime remains unarmed | Chaos/security API test |
| Data exposure | Local SQLite and CLI reports | System prompts, absolute model paths, raw trace payloads, run metadata, and failure details omitted at API boundary | Safe-view/trace tests |
| API boundary | Direct Python calls only before Stage 15 | Loopback HTTP/JSON + SSE and OpenAPI provide the accepted frontend contract | `runtime/api/`, Stage 15 report |
| Tests/benchmarks | 138 tests plus security result | 147 tests plus retained 16-operation external API result | `tests/test_api.py`, Stage 15 result/report |
| Decisions/risks | ADR-0015 and application-security caveats | ADR-0016 plus production-server, connection, restart, and retention limitations | `docs/adr/`, `docs/risks.md` |
| Acceptance | Separate subsystem evidence only | One 14-command gate, 14/14 required PASS, scoped maturity matrix, and release recommendation | Acceptance JSON/report, ADR-0017 |
| Release identity | 0.15.0 API-ready backend | 0.16.0 verified backend release candidate | `pyproject.toml`, acceptance result |
| Frontend research | Backend accepted; no direction selected | 28-source current research, Systems Cartography recommendation, stack/performance/accessibility constraints, no UI implementation | `docs/frontend-research.md` |
| Frontend shell | Stage 18 endpoint placeholders | Twelve URL-addressable domains plus real `/runtime` pulse, task launch/inspection/cancellation, and ordered lifecycle rail | `apps/web/src/`, Stage 19 report |
| Design system | Proposed visual direction | Executable tokens, eleven status states, two density modes, motion/data-viz/a11y contracts, and interactive component route | `docs/frontend-design-system.md`, `/design-system` |
| Frontend server state | No API fetch or stream | Typed Query ownership for six inspection resources, task mutations/polling, URL selection, and bounded native EventSource reconciliation | `api/`, `query/`, `useTaskEvents.ts` |
| Frontend validation | 5/5 shell tests and 102,802-byte gzip shell | 7/7 runtime tests, axe scan, build/bundle gate, and retained real proxy/API/SSE smoke | `App.test.tsx`, `stage19-smoke.mjs`, retained JSON |
| Agent/scheduler projection | Stage 19 endpoint placeholders and raw runtime pulse | Real role/tool catalog, selected state/handoff, admission, worker/queue map, request timing/ledger, cancellation, and retained metadata fallback | `components/scheduler/`, Stage 20 report |
| Stage 20 validation | 7/7 runtime tests | 12/12 component tests with three axe route scans plus real proxy/API/SSE state-and-dispatch smoke | `App.test.tsx`, `stage20-smoke.mjs`, retained JSON |
| Trace/replay projection | Stage 11 safe trace/replay backend and Stage 18 endpoint placeholder | Selected-task execution timeline, URL-addressable expansion, filters/search, timestamp-gap bars, redacted hashes, and explicit side-effect-free replay outcomes | `components/trace/`, Stage 21 report, ADR-0021 |
| Stage 21 validation | 12/12 Stage 20 component tests | 18/18 component tests with four axe route scans, a 10,000-step/100-row DOM bound, and real proxy/API trace/replay smoke | `App.test.tsx`, `stage21-smoke.mjs`, retained JSON |
| Hardware/performance projection | Runtime pulse and Stage 18 endpoint placeholders | Source-labelled capacity board, inference/scheduler signals, eight distributions, selected profile/budget, model candidates, and bounded recent-task trends on `/hardware` and `/metrics` | `components/performance/`, Stage 22 report, ADR-0022 |
| Stage 22 validation | 18/18 Stage 21 component tests | 23/23 component tests with six axe route scans plus real hardware/model/scheduler/task/history smoke | `App.test.tsx`, `stage22-smoke.mjs`, retained JSON |
| Experiment API discovery | Confirmed chaos POST and retained security GET | Server-owned chaos/security catalogs plus confirmed selected security execution and atomic retained report | `runtime/api/`, `runtime/security/runner.py`, API tests, ADR-0023 |
| Chaos projection | Stage 18 endpoint placeholder | Maximum-three selection, isolation confirmation, reliability envelope, expected/actual propagation, containment, trace/latency, and recovery evidence | `components/chaos/`, `/chaos`, Stage 23 report |
| Security projection | Stage 18 endpoint placeholder | Selected deterministic execution, retained/new report ownership, summary/disclaimer, category-filtered attack/blocked-action evidence | `components/chaos/`, `/security`, Stage 23 report |
| Stage 23 validation | 23/23 Stage 22 component tests | 28/28 component tests with eight axe route scans plus three-fault/all-fourteen-case real proxy smoke | `App.test.tsx`, `stage23-smoke.mjs`, retained JSON |
| Interaction layer | Stage 23 native rail, shallow History adapter, and resizable split | React Aria command palette, bounded native View Transitions, reduced-motion fallback, contextual route/task/source facts, progressive guidance, and pane reset | `components/interaction/`, `interaction.css`, ADR-0024 |
| Stage 24 validation | 28/28 Stage 23 component tests and 130,676-byte gzip JS | 34/34 tests including command/motion/open-palette axe, six-route smoke, and 149,836-byte gzip JS gate | `App.test.tsx`, `stage24-smoke.mjs`, retained JSON |
| Responsive/accessibility/performance hardening | Stage 24 viewport/media rules, jsdom accessibility, 200/30 stream and 100-row trace bounds | Five-size browser reflow, explicit focus/status/busy semantics, passing contrast tokens, container reflow, accurate slow-loading language, and frame-batched SSE | App shell/runtime/event hook/styles, ADR-0025 |
| Stage 25 validation | 34/34 Stage 24 tests and six-route smoke | 38/38 tests, 500-event/10,000-step/slow-response stress, twelve-route contrast/contract smoke, browser accessibility snapshot, and 150,118-byte gzip JS gate | `App.test.tsx`, `stage25-smoke.mjs`, retained JSON |
| Safe tool API/UI | Python/CLI-only exact-grant tool runtime | Server-owned `GET /v1/tools`, bounded `POST /v1/tools/execute`, and Runtime Safe Tool Probe with durable task/trace evidence | `runtime/api/`, `ToolProbe.tsx`, API/component tests |
| Durable frontend recovery | Completed tasks inspectable through the API with a persistence-specific envelope | Persisted inference results normalize to the live task-result shape with reconstructed state history, so URL-selected tasks render after API restart | `runtime/api/manager.py`, restart API/browser tests |
| Stage 26 product acceptance | Independent backend/frontend gates and manual browser evidence | One isolated gate combines 154 backend tests, real model, 39 frontend tests, build/bundle, eight browser routes, five failures, tool trace/replay, outage/recovery, and restart durability | `run_stage26_product_acceptance.py`, `stage26-browser.mjs`, retained JSON, ADR-0026 |
| Release identity | Stage 26 frontend 0.26.0 | Stage 27 frontend 0.27.0; portfolio/interview release of the accepted single-user loopback product, overall maturity still `PARTIAL` | `apps/web/package.json`, Stage 27 report |
| Stage 27 portfolio release | Stage evidence spread across chronological reports | Recruiter-first documentation, five real workbench screenshots, a five-minute demo, systems/security/frontend rationale, failed experiments, interview Q&A, and executable evidence/link/image validation | `docs/portfolio/`, `docs/assets/portfolio/`, `configs/portfolio-release.json`, `validate_portfolio_release.py`, ADR-0027 |
| Windows setup/launcher | Backend-first Stage 25 launcher with health/mode checks | Stage 27 exact `npm ci`, optional Ollama → backend → frontend order, tool-contract check, tracked frontend release marker, and fail-safe stale-service rejection | `setup_and_run.bat`, `apps/web/public/local-ai-release.json`, `test_setup_launcher.py` |

## Current and planned folder convention

The following remains a boundary guide. Existing folders are evidence of only
the files listed above; later subdirectories are not implementation claims.

```text
apps/             Approved local applications
  web/            Stage 27 portfolio-released React/Vite workbench with reproducible browser capture
runtime/          Inspectable runtime implementation
  api/            Current loopback backend adapter and application service
  agents/         Agent identity and behavior contracts
  inference/      Local inference backend abstraction and adapters
  scheduler/      Request ordering and cancellation
  routing/        Model registry, routing, and compute budgets
  policy/         Admission and permission decisions
  persistence/    SQLite records, checkpoints, and bounded recovery
  tools/          Restricted tool registry/execution
  tracing/        Deterministic event and replay structures
  faults/         Controlled fault injection
  security/       Deterministic security boundaries and adversarial evidence
  metrics/        Runtime and inference telemetry
native/           Evidence-justified native optimizations only
tests/            Unit, integration, failure, security, and acceptance tests
benchmarks/       Reproducible workloads, configs, and recorded results
configs/          Typed, versioned, non-secret configuration
scripts/          Reproducible developer and verification commands
docs/             Architecture, decisions, experiments, research, and reports
```

## Ownership rules

- `PROJECT_STATE.md` is updated at every stage boundary and never describes planned work as complete.
- Runtime interfaces live with the runtime, not in the API or UI.
- External adapters depend on core contracts; core contracts do not depend on a specific model server or web framework.
- Generated model files, caches, secrets, and local databases stay ignored.
- Benchmark workloads, configurations, and compact JSON results are tracked;
  large profiler captures require an explicit retention decision.
