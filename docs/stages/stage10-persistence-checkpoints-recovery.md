# Stage 10 — Persistence, Checkpoints & Recovery

## What this stage is for

Stage 10 makes runtime evidence survive process exit and defines one safe,
testable restart boundary. It does not pretend arbitrary model or tool side
effects can be resumed exactly.

## Component upgrade map

| Component | What it does in Stage 10 | Upgrade over Stage 9 |
| --- | --- | --- |
| SQLite schema | Stores agents, tasks, transitions, checkpoints, events, metrics, steps, model configurations, tool calls, outputs, and recovery attempts | Replaces process-local execution evidence with versioned durable records |
| Protocol adapters | Present narrow agent/event/metric/checkpoint/state interfaces over one database | Preserves existing dependency boundaries while sharing transactions/storage |
| Persistent state machine | Applies the existing legal graph inside `BEGIN IMMEDIATE` transactions | Reconstructs current state/history after restart and rolls back illegal changes |
| Recovery checkpoint | Commits `recovery_ready` while still in `PLANNING`, before model/tool invocation | Establishes the only automatically retryable boundary |
| `RECOVERING` state | Records restart ownership before planning resumes | Makes recovery visible in the same state history instead of hiding a re-run |
| Recovery ledger | Records attempt start, checkpoint, completion/failure, and timestamps | Preserves prior history and prevents recovery from looking like a fresh task |
| Durable tool/output records | Stores typed arguments/results/errors and inference/tool outputs | Makes completed work inspectable after restart |

## Schema and transaction behavior

- Schema version: 1.
- SQLite settings: foreign keys on, 5,000 ms busy timeout, WAL journal, `FULL` synchronous mode.
- Migrations are transactional and idempotent; a database newer than the runtime is rejected.
- JSON is explicit and sorted; runtime objects are reconstructed through typed constructors.
- Illegal state transitions leave both `current_state` and transition count unchanged.
- Each operation uses a short connection/transaction, avoiding a process-owned
  connection that could remain locked after termination.

## Recovery semantics

Automatically recoverable:

```text
CREATED -> PLANNING -> [recovery_ready committed]
process interrupted
PLANNING -> RECOVERING -> PLANNING -> EXECUTING -> VALIDATING -> COMPLETED
```

Not automatically recovered:

- terminal tasks;
- `EXECUTING`, `WAITING_FOR_TOOL`, or other in-flight side-effect boundaries;
- planning tasks without the exact `recovery_ready` marker;
- a second crash after entering `RECOVERING`.

These records remain durable for inspection/manual resolution. This prevents
automatic duplication of a completed or ambiguous model/tool action.

## Demonstrated recovery

`python -m runtime.recovery_cli` launched a separate worker, persisted one task
at `recovery_ready`, then forcibly terminated the worker with exit code 1. A new
runtime opened the same database and completed the original task with history:

```text
created -> planning -> recovering -> planning -> executing -> validating -> completed
```

Retained result: `benchmarks/results/stage10-recovery-20260824T131728Z.json`.

The retained database evidence reported:

- `integrity_check`: `ok`;
- schema version 1;
- 1 task, 7 transitions, 8 checkpoints, 24 lifecycle events, 24 metric events,
  18 execution steps, 2 model-configuration snapshots, 1 output, and 1 recovery attempt;
- zero real LLM calls because the crash/recovery proof uses the deterministic stub.

## Real inference validation

The real Stage 10 runtime completed the technical explainer through routing,
budgeting, `performance` profile admission, scheduling, llama.cpp, output
persistence, and shutdown:

- task elapsed: 2,891.000 ms;
- backend total / TTFT: 2,125.300 / 1,420.839 ms;
- throughput: 106.76 tokens/s;
- peak child RAM / VRAM delta: 1,343.590 / 1,189 MiB;
- durable records: 1 task, 5 transitions, 5 checkpoints, 21 lifecycle events,
  17 execution steps, 1 model configuration, and 1 output;
- a new composition reconstructed `completed` plus all five transitions and
  returned `integrity_check: ok` without starting the model.

## Verification

- Stage 10 focused tests: 11 passed.
- Final full suite: 99 passed in 6.524 seconds.
- Killed-process recovery CLI and retained runner: exit 0.
- Real durable llama.cpp execution and restart inspection: exit 0.
- Bytecode compilation, package dry run for version 0.10.0, runtime smoke test,
  and `git diff --check`: exit 0.

## Limits retained

- Recovery restarts from a pre-invocation checkpoint; it does not resume native token generation.
- SQLite is single-host state and does not coordinate multiple runtime processes as a cluster.
- Scheduler queue/worker internals are not reconstructed; the task is resubmitted after safe recovery.
- Output/state completion is written in adjacent transactions, so a crash in that
  narrow interval may leave a terminal task without an output; safety policy
  refuses automatic duplication and leaves manual inspection.
- Stage 11 owns structured run/step IDs, hashes, and deterministic replay semantics.
