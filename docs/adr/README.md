# Architecture Decision Records

ADRs preserve decisions that materially affect architecture, security,
performance, reproducibility, or stage boundaries.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-stage-gated-modular-backend-first.md) | Accepted | Stage-gated, backend-first, Python-first modular runtime |
| [0002](0002-typed-protocols-and-stdlib-skeleton.md) | Accepted | Typed protocols and a standard-library synchronous skeleton |
| [0003](0003-pinned-llama-cpp-qwen-baseline.md) | Accepted | Pinned llama.cpp subprocess and Qwen GGUF baseline |
| [0004](0004-registered-agent-runtime-and-lifecycle-events.md) | Accepted | Registered agents and explicit lifecycle events |
| [0005](0005-validated-execution-state-machine.md) | Accepted | Validated execution state machine and typed terminal failures |
| [0006](0006-default-deny-bounded-tool-runtime.md) | Accepted | Default-deny typed tools with root containment and cooperative bounds |
| [0007](0007-bounded-aged-priority-scheduler.md) | Accepted | Bounded FIFO/priority scheduler with aging and end-to-end deadlines |
| [0008](0008-conservative-pre-scheduler-memory-admission.md) | Accepted | Source-aware hardware profiling and conservative pre-scheduler memory admission |
| [0009](0009-discrete-re-admitted-inference-profiles.md) | Accepted | Discrete workload profiles with mandatory re-admission and measured tradeoffs |
| [0010](0010-explainable-availability-gated-model-routing.md) | Accepted | Availability-gated model routing with explainable candidates and task compute budgets |
| [0011](0011-sqlite-checkpoints-and-pre-invocation-recovery.md) | Accepted | Versioned SQLite durability and explicit pre-invocation recovery |
| [0012](0012-hash-chained-traces-and-bounded-replay.md) | Accepted | Hash-chained task traces with classified, side-effect-free replay |
| [0013](0013-sqlite-windowed-observability-snapshots.md) | Accepted | Windowed SQLite aggregation plus optional live scheduler/hardware snapshots |
| [0014](0014-bounded-protocol-fault-injection.md) | Accepted | Explicitly armed, count-bounded fault adapters and process recovery experiments |
| [0015](0015-deterministic-security-boundaries.md) | Accepted | Deterministic least-privilege security boundaries and repeatable adversarial evidence |
| [0016](0016-loopback-stdlib-http-json-sse-api.md) | Accepted | Versioned loopback HTTP/JSON and SSE over a transport-independent runtime service |
| [0017](0017-scoped-evidence-based-backend-acceptance.md) | Accepted | Binary required checks plus honest scoped subsystem maturity classifications |
| [0018](0018-systems-cartography-web-shell.md) | Accepted | Systems Cartography local React shell with explicit state boundaries and bundle budget |
| [0019](0019-real-loopback-query-and-sse-client.md) | Accepted | Real loopback query ownership, URL task selection, and bounded SSE lifecycle client |
| [0020](0020-task-scoped-agent-scheduler-projections.md) | Accepted | Task-scoped agent state and scheduler evidence projections with retained dispatch fallback |
| [0021](0021-redacted-trace-projection-and-explicit-replay.md) | Accepted | Redacted task-trace projection with URL step inspection and explicit side-effect-free replay |
| [0022](0022-source-labelled-performance-projection.md) | Accepted | Source-labelled hardware and performance projection without duplicate live probes or invented samples |
| [0023](0023-server-catalogued-confirmed-experiment-ui.md) | Accepted | Server-owned experiment catalogs with explicit confirmation, isolation, and non-certifying visual evidence |
| [0024](0024-native-progressive-interaction-layer.md) | Accepted | Keyboard-first command navigation and bounded native route transitions with immediate fallbacks |
| [0025](0025-container-aware-accessible-bounded-rendering.md) | Accepted | Container-aware reflow, explicit accessible focus/status, passing contrast, and frame-batched bounded streams |

## Process

1. Copy `template.md` and assign the next four-digit number.
2. Record context and evidence available at decision time.
3. Compare real alternatives, including the cost of doing nothing.
4. Mark the status `Proposed`, `Accepted`, `Superseded`, or `Rejected`.
5. Do not rewrite accepted history; add a superseding ADR when a decision changes.
6. Link measurements, tests, failed experiments, and successor ADRs when available.
