# Repository Map

## Reconstruction result

At the start of Stage 0, commit `67ef780` contained one tracked file:
`README.md` with only the project heading. The `main` worktree was clean and
matched `origin/main`. There were no source directories, tests, configuration
files, dependency manifests, architecture documents, or TODO/FIXME markers.

## Structure after Stage 11

```text
Local-AI-System-Lab/
├── .gitignore
├── README.md                          # Entry point, demo, and approval status
├── PROJECT_STATE.md                   # Repository source of truth
├── pyproject.toml                     # Python >=3.10 package metadata and CLIs
├── configs/
│   ├── inference-baseline.json        # Pinned backend/model/runtime settings
│   ├── admission-baseline.json        # Model metadata, estimator, reserves, calibration
│   ├── inference-profiles.json        # Typed adaptive resource-profile catalog
│   ├── model-registry.json            # Model availability and workload budgets
│   └── persistence.json               # SQLite path, timeout, journal, durability mode
├── benchmarks/
│   ├── __init__.py
│   ├── run_stage2_baseline.py         # Reproducible benchmark runner
│   ├── run_stage8_profiles.py         # Same-workload resource-profile runner
│   ├── run_stage9_routing.py          # Controlled explained route comparison
│   ├── run_stage10_recovery.py        # Killed-process recovery evidence runner
│   ├── run_stage11_trace_replay.py    # Trace/replay/comparison evidence runner
│   ├── prompts/stage2-baseline.json   # Five-prompt tracked workload
│   ├── results/stage2-baseline-20260823T180550Z.json
│   ├── results/stage8-profile-comparison-20260824T121616Z.json # Exploratory zero-layer run
│   ├── results/stage8-profile-comparison-20260824T122355Z.json # Final explicit-device run
│   ├── results/stage9-routing-20260824T124057Z.json # Controlled route result
│   ├── results/stage10-recovery-20260824T131728Z.json # Retained restart result
│   └── results/stage11-trace-replay-20260824T143744Z.json # Retained replay result
├── docs/
│   ├── architecture.md                # Implemented/deferred component boundaries
│   ├── development.md                 # Reproducible run/test/check commands
│   ├── environment.md                 # Measured workstation/tool baseline
│   ├── repository-map.md              # This inventory
│   ├── risks.md                       # Evidence-based risk register
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
│   │   └── stage11-execution-trace-deterministic-replay.md
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
│       └── template.md
├── runtime/
│   ├── __init__.py                    # Public runtime API through Stage 11
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

## Component inventory

| Area | State after Stage 10 | State after Stage 11 | Evidence |
| --- | --- | --- | --- |
| Repository | Persistence/recovery report and 0.10.0 identity | Adds trace result/report, ADR-0012, and 0.11.0 identity | README, trace result, ADR index |
| Runtime | Durable routed execution plus bounded recovery | Adds task-scoped trace protocol and replay access | Trace/replay tests and CLI |
| Inference | Outputs/configuration durable | Adds hashed prompt/configuration/output boundaries; generation remains nondeterministic | Real Stage 11 trace/replay |
| Scheduler/router/policy | Durable lifecycle evidence | Adds classified actor/component trace steps and semantic comparison | Retained two-run result |
| Tools | Durable request/result/error/output ledger | Adds side-effect classification and replay skip behavior | Tool replay test |
| Persistence/tracing/metrics | SQLite schema v1, no trace semantics | Schema v2 hash-chains run steps and stores replay reports | Migration, tamper, restart, replay tests |
| API/frontend | Missing | Intentionally deferred | `PROJECT_STATE.md` |
| Tests/benchmarks | 99 tests and recovery result | 108 tests, retained trace comparison, and real traced inference | `tests/`, Stage 11 result/report |
| Environment evidence | SQLite integrity/restart evidence | Adds real 18-step Qwen trace and replay evidence | Stage 11 report |
| Decisions/risks | ADR-0011 recovery limits | ADR-0012 plus replay-authenticity/payload-retention caveats | `docs/adr/`, `docs/risks.md` |

## Current and planned folder convention

The following remains a boundary guide. Existing folders are evidence of only
the files listed above; later subdirectories are not implementation claims.

```text
apps/             External entry points; API later, production web only after gate
runtime/          Inspectable runtime implementation
  agents/         Agent identity and behavior contracts
  inference/      Local inference backend abstraction and adapters
  scheduler/      Request ordering and cancellation
  routing/        Model registry, routing, and compute budgets
  policy/         Admission and permission decisions
  persistence/    SQLite records, checkpoints, and bounded recovery
  tools/          Restricted tool registry/execution
  tracing/        Deterministic event and replay structures
  faults/         Controlled fault injection
  metrics/        Runtime and inference telemetry
native/           Evidence-justified native optimizations only
tests/            Unit, integration, failure, security, and acceptance tests
benchmarks/       Reproducible workloads, configs, and recorded results
configs/          Typed, versioned, non-secret configuration
scripts/          Reproducible developer and verification commands
docs/             Architecture, decisions, experiments, and reports
```

## Ownership rules

- `PROJECT_STATE.md` is updated at every stage boundary and never describes planned work as complete.
- Runtime interfaces live with the runtime, not in the API or UI.
- External adapters depend on core contracts; core contracts do not depend on a specific model server or web framework.
- Generated model files, caches, secrets, and local databases stay ignored.
- Benchmark workloads, configurations, and compact JSON results are tracked;
  large profiler captures require an explicit retention decision.
