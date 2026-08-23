# Repository Map

## Reconstruction result

At the start of Stage 0, commit `67ef780` contained one tracked file:
`README.md` with only the project heading. The `main` worktree was clean and
matched `origin/main`. There were no source directories, tests, configuration
files, dependency manifests, architecture documents, or TODO/FIXME markers.

## Structure after Stage 1

```text
Local-AI-System-Lab/
├── .gitignore
├── README.md                          # Entry point, demo, and approval status
├── PROJECT_STATE.md                   # Repository source of truth
├── pyproject.toml                     # Python >=3.10 package metadata; zero dependencies
├── docs/
│   ├── architecture.md                # Implemented/deferred component boundaries
│   ├── development.md                 # Reproducible run/test/check commands
│   ├── environment.md                 # Measured workstation/tool baseline
│   ├── repository-map.md              # This inventory
│   ├── risks.md                       # Evidence-based risk register
│   └── adr/
│       ├── README.md                  # ADR process and index
│       ├── 0001-stage-gated-modular-backend-first.md
│       ├── 0002-typed-protocols-and-stdlib-skeleton.md
│       └── template.md
├── runtime/
│   ├── __init__.py                    # Public Stage 1 API
│   ├── __main__.py                    # `python -m runtime` entry point
│   ├── cli.py                         # JSON lifecycle demonstration
│   ├── config.py                      # Validated typed configuration
│   ├── engine.py                      # AgentRuntime orchestration
│   ├── errors.py                      # Structured error hierarchy
│   ├── factory.py                     # Dependency composition root
│   ├── in_memory.py                   # Deterministic stub implementations
│   ├── interfaces.py                  # Replaceable component protocols
│   └── models.py                      # Typed domain/component data
├── scripts/
│   └── check_environment.ps1          # Read-only environment inventory
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_config_and_errors.py
    ├── test_interfaces.py
    └── test_runtime.py
```

No empty future directories are added merely to imply implementation.

## Component inventory

| Area | State before Stage 1 | State after Stage 1 | Evidence |
| --- | --- | --- | --- |
| Repository | Documentation baseline | Python package and reproducible commands | `pyproject.toml`, development docs |
| Runtime | Missing | Synchronous start/create/execute/shutdown skeleton | CLI and integration tests |
| Inference | Missing | Protocol plus no-LLM deterministic stub | Stub output and `real_llm_calls: 0` |
| Scheduler/router/policy | Boundaries documented | Protocols plus inline/static/identity implementations | Interface/runtime tests |
| Persistence/tracing/metrics | Boundaries documented | Process-local checkpoint/metric protocols and stores | Runtime tests; no durability claim |
| API/frontend | Missing | Intentionally deferred | `PROJECT_STATE.md` |
| Tests/benchmarks | Missing | 13 standard-library tests; no benchmark harness | `tests/` and executed test command |
| Environment evidence | Recorded | Retained and reproducible | `docs/environment.md`, script |
| Decisions/risks | Stage 0 records | Stage 1 evidence and ADR-0002 added | `docs/adr/`, `docs/risks.md` |

## Current and planned folder convention

The following remains a boundary guide. Only `runtime/`, `tests/`, `scripts/`,
and `docs/` currently exist; later subdirectories are not implementation claims.

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
- Generated model files, caches, secrets, local databases, and benchmark raw data require explicit retention rules before being committed.
