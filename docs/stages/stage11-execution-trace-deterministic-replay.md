# Stage 11 — Execution Trace & Deterministic Replay

## What this stage is for

Stage 11 turns Stage 10's durable execution evidence into coherent task runs
that can be inspected, integrity-checked, replayed where deterministic, and
compared without misrepresenting model generation or tool effects.

## Component upgrade map

| Component | What it does in Stage 11 | Upgrade over Stage 10 |
| --- | --- | --- |
| SQLite schema v2 | Stores trace runs, ordered steps, chain hashes, and replay reports | Adds forward v1-to-v2 migration and durable trace identity |
| Trace classifier | Labels deterministic, nondeterministic, observational, and side-effecting steps | Makes replay safety explicit per event |
| Canonical hasher | Produces exact input/output, normalized semantic, previous, and envelope SHA-256 hashes | Detects mutation/reordering and supports semantic comparison |
| Trace store | Loads runs/steps after restart through a narrow protocol | Groups loose Stage 10 evidence into inspectable executions |
| Replay engine | Verifies chain/payloads and reconstructs deterministic state transitions | Replays orchestration without repeating model/tool effects |
| Comparator | Aligns repeated event names and classifies matches/divergences/observations/missing steps | Compares two executions without treating nondeterminism as failure |
| Trace CLI | Demonstrates inspect, replay, compare, and a two-run scenario | Makes the capability runnable without internal Python calls |

## Trace contract

Each task-scoped trace step contains:

- run ID, ordinal, and stable UUID step ID;
- UTC timestamp and actor/component;
- event name and determinism class;
- canonical input/output payloads and SHA-256 hashes;
- normalized semantic hash for cross-run comparison;
- source/destination state where applicable;
- model and runtime-configuration hash;
- structured failure metadata where applicable;
- previous-step hash and full envelope hash.

Stable means repeatable from the same run ID, ordinal, and event name. It does
not mean two independent runs share IDs.

## Replay contract

Replay is deliberately side-effect-free:

- deterministic records are hash-verified and state transitions are reduced into
  a reconstructed state;
- model generation is nondeterministic and is integrity-checked only;
- scheduler/hardware/profile observations are not recreated;
- tool requests/results are recorded but never invoked again;
- a broken payload, step ID, sequence, previous hash, or envelope hash fails integrity.

This is deterministic execution-evidence replay, not native llama.cpp token replay.

## Demonstrated evidence

The retained `stage11-trace-replay-20260824T143744Z.json` contains two equivalent
stub-backed executions:

- schema version 2 and SQLite integrity `ok`;
- 15 trace steps per run;
- per run: 10 deterministic, 3 nondeterministic, and 2 observational steps;
- replay reconstructed `completed` with 10 matches, 5 observed-only steps,
  zero integrity failures, and zero new model calls;
- comparison found 10 deterministic matches, zero divergences, five
  nondeterministic observations, and zero missing steps.

The real Qwen2.5 1.5B validation produced one 18-step trace:

- 11 deterministic, 3 nondeterministic, and 4 observational steps;
- replay reconstructed `completed` with 11 matches and 7 observed-only steps;
- chain and SQLite integrity both passed;
- inference measured 2,865.074 ms total, 1,989.471 ms TTFT, 94.53 tokens/s,
  1,345.855 MiB peak RAM, and 1,189 MiB VRAM delta.

## Verification

- Persistence plus Stage 11 focused tests: 20 passed.
- Final full suite: 108 passed in 13.895 seconds.
- Retained trace/replay runner: exit 0.
- Real llama.cpp trace inspection and bounded replay: exit 0.
- Bytecode compilation, package dry run for version 0.11.0, runtime smoke test,
  and `git diff --check`: exit 0.

## Limits retained

- The chain is tamper-evident, not cryptographically authenticated against an
  attacker who can recompute every hash.
- Trace payloads can contain sensitive local inputs/outputs; redaction and
  retention controls are not implemented.
- Pre-Stage-11 rows are migrated but not fabricated into historical traces.
- Comparison is structural/semantic hash comparison, not output-quality evaluation.
- Aggregation, live telemetry, trace export, and retention policy belong to Stage 12.
