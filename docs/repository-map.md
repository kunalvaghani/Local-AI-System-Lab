# Repository Map

## Reconstruction result

At the start of Stage 0, commit `67ef780` contained one tracked file:
`README.md` with only the project heading. The `main` worktree was clean and
matched `origin/main`. There were no source directories, tests, configuration
files, dependency manifests, architecture documents, or TODO/FIXME markers.

## Structure after Stage 2

```text
Local-AI-System-Lab/
├── .gitignore
├── README.md                          # Entry point, demo, and approval status
├── PROJECT_STATE.md                   # Repository source of truth
├── pyproject.toml                     # Python >=3.10 package metadata and CLIs
├── configs/
│   └── inference-baseline.json        # Pinned backend/model/runtime settings
├── benchmarks/
│   ├── __init__.py
│   ├── run_stage2_baseline.py         # Reproducible benchmark runner
│   ├── prompts/stage2-baseline.json   # Five-prompt tracked workload
│   └── results/stage2-baseline-20260823T180550Z.json
├── docs/
│   ├── architecture.md                # Implemented/deferred component boundaries
│   ├── development.md                 # Reproducible run/test/check commands
│   ├── environment.md                 # Measured workstation/tool baseline
│   ├── repository-map.md              # This inventory
│   ├── risks.md                       # Evidence-based risk register
│   ├── benchmarks/
│   │   └── stage2-local-inference-baseline.md
│   └── adr/
│       ├── README.md                  # ADR process and index
│       ├── 0001-stage-gated-modular-backend-first.md
│       ├── 0002-typed-protocols-and-stdlib-skeleton.md
│       ├── 0003-pinned-llama-cpp-qwen-baseline.md
│       └── template.md
├── runtime/
│   ├── __init__.py                    # Public Stage 1 API
│   ├── __main__.py                    # `python -m runtime` entry point
│   ├── cli.py                         # JSON lifecycle demonstration
│   ├── config.py                      # Validated typed configuration
│   ├── cancellation.py                # Thread-safe cancellation token
│   ├── engine.py                      # AgentRuntime orchestration
│   ├── errors.py                      # Structured error hierarchy
│   ├── factory.py                     # Dependency composition root
│   ├── in_memory.py                   # Deterministic stub implementations
│   ├── interfaces.py                  # Replaceable component protocols
│   ├── inference_cli.py               # Real inference/stream/cancel CLI
│   ├── models.py                      # Typed domain/component data
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
    ├── test_cli.py
    ├── test_config_and_errors.py
    ├── test_interfaces.py
    ├── test_inference_metrics.py
    ├── test_llama_cpp_backend.py
    └── test_runtime.py
```

Ignored `tools/` and `models/` directories contain the verified native binaries
and GGUF file; they are reproducible artifacts, not source. No empty future
directories are added merely to imply implementation.

## Component inventory

| Area | State after Stage 1 | State after Stage 2 | Evidence |
| --- | --- | --- | --- |
| Repository | Python skeleton | Pinned inference config/setup and benchmark artifacts | Config, setup script, development docs |
| Runtime | Synchronous lifecycle skeleton | Skeleton plus cancellation and measured inference result data | Unit/integration tests |
| Inference | Protocol plus deterministic stub | Real llama.cpp/GGUF streaming adapter; stub retained | Real CLI output and backend tests |
| Scheduler/router/policy | Boundaries documented | Protocols plus inline/static/identity implementations | Interface/runtime tests |
| Persistence/tracing/metrics | Boundaries documented | Process-local checkpoint/metric protocols and stores | Runtime tests; no durability claim |
| API/frontend | Missing | Intentionally deferred | `PROJECT_STATE.md` |
| Tests/benchmarks | 13 tests; no inference benchmark | 19 tests and a tracked five-run real baseline | `tests/`, `benchmarks/`, benchmark report |
| Environment evidence | Recorded | Retained and reproducible | `docs/environment.md`, script |
| Decisions/risks | Stage 1 evidence and ADR-0002 | Stage 2 evidence, ADR-0003, and updated risks | `docs/adr/`, `docs/risks.md` |

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
  checkpoints/    Checkpoint contracts and later persistence
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
