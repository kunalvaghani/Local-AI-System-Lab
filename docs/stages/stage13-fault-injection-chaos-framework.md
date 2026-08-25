# Stage 13 — Fault Injection / Chaos Framework

## What this stage is for

Stage 13 turns failure behavior into a repeatable experiment. It deliberately
activates one bounded fault at a named subsystem boundary, verifies the resulting
state/error/trace, and measures latency, containment, task completion, recovery,
observability, and database integrity. It does not claim that every failure is
recoverable or that simulated faults reproduce every physical failure mode.

## Component upgrade map

| Component | What it does in Stage 13 | Upgrade over Stage 12 |
| --- | --- | --- |
| Chaos configuration | Declares nine typed scenarios, delays, and injection caps; defaults to disabled | Makes failure experiments reproducible and bounded |
| Fault controller | Matches explicit protocol points, enforces counts, delays, and records `fault.injected` metrics | Adds task-correlated activation evidence to observability |
| Inference adapter | Injects typed timeout, empty output, context overflow, and simulated OOM | Exercises existing model failure-state contracts without loading a model |
| Tool adapter | Injects timeout, corrupt identity, and wrong argument types | Tests execution and post-result validation separately |
| Persistence adapter | Fails the terminal output write after the completed transition | Reproduces and measures the known atomicity gap rather than hiding it |
| Process harness | Terminates a worker after `recovery_ready`, restarts, and recovers the same task | Converts Stage 10 recovery into a configurable chaos scenario |
| Chaos report | Compares expected/actual state and error, latency, containment, recovery, traces, telemetry, and integrity | Unifies previously separate failure tests into one machine-readable result |
| Stage 13 factory | Composes adapters into deterministic and real runtimes while remaining inert by default | Preserves ordinary Stage 12 behavior and requires explicit arming |

## Controlled scenarios

| Scenario | Injected boundary | Expected result | Retained result |
| --- | --- | --- | --- |
| Model timeout | `inference.generate` | `TIMEOUT` / `task_timeout` | Matched |
| Invalid model output | `inference.generate` result | `INVALID_OUTPUT` / `invalid_output` | Matched |
| Context overflow | `inference.generate` | `CONTEXT_OVERFLOW` | Matched |
| Simulated OOM | `inference.generate` | `OUT_OF_MEMORY` | Matched |
| Tool timeout | `tool.execute` | `TIMEOUT` / `task_timeout` | Matched |
| Corrupted tool result | `tool.execute` result | `INVALID_OUTPUT` | Matched |
| Malformed tool call | `tool.execute` arguments | `TOOL_FAILED` | Matched |
| Database result failure | `persistence.save_task_result` | Detect completed/output gap | Matched, not contained |
| Agent crash | `recovery.checkpoint_ready` | Worker dies; restart completes same task | Matched and recovered |

## Demonstrated evidence

The retained `stage13-chaos-20260824T193424Z.json` contains:

- nine scenarios and nine bounded injections;
- 100% expected state/error outcome matching;
- eight contained scenarios, or 88.889%;
- one recovery attempt and one success, or 100%;
- one scenario completing without an error after recovery, or 11.111% task
  completion across intentionally failing scenarios;
- zero real LLM calls and SQLite integrity `ok`;
- 11 durable tasks, nine `fault.injected` metrics, seven task failures, one
  recovery, 11 trace runs, and 140 trace steps;
- 9.457 ms durable observability collection.

No-fault deterministic baselines measured 614.179 ms for inference and 562.478
ms for the read-only tool. Added latency ranged from -160.674 ms to 1,034.265
ms, with P50 -71.797 ms and P95 611.597 ms. Negative values mean a fault failed
before the successful baseline finished; they are not throughput improvements.
The worker termination plus recovery took 1,648.444 ms.

## Usage and safety gate

Inspect help without arming faults:

```powershell
python -m runtime.chaos_cli --help
```

Run one selected scenario or the complete suite:

```powershell
python -m runtime.chaos_cli --execute --scenario model-timeout
python -m runtime.chaos_cli --execute
python -m benchmarks.run_stage13_chaos
```

Omitting `--execute` returns a structured refusal and does not create a database.
The tracked configuration also defaults to `enabled: false`. Normal
`build_stage13_runtime()` composition therefore has inert adapters.

## Measured gap

The database-result failure happens after the state transition to `COMPLETED`
but before the output row is saved. The caller receives
`database_operation_failed`, while durable state remains `completed` and no
output exists. Chaos detected the exact R-32 crash window, so the scenario is an
expected observation but `contained: false`. Fixing it requires a combined
terminal-state/output transaction or repair protocol and is retained as debt.

## Limits retained

- The timeout/OOM/context faults are controlled protocol injections, not actual
  exhausted GPU memory or a hung native llama.cpp process.
- Only the agent-crash scenario terminates a real OS process.
- Unsafe in-flight model/tool failures remain terminal and are not retried.
- The configured delay cap is 1,000 ms and every tracked scenario injects once.
- Quality impact is `null`; semantic evaluation is not meaningful for this
  deterministic containment suite.
- Stage 14 security and adversarial testing has not started.
