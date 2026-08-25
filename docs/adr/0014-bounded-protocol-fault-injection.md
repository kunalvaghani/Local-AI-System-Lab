# ADR-0014 — Bounded Protocol-Level Fault Injection

- Status: Accepted
- Date: 2026-08-25

## Context

The runtime already classifies model, tool, scheduler, persistence, and recovery
failures, but those paths were exercised by separate unit fixtures. Stage 13
needs one configurable framework that can deliberately activate faults, retain
task identity and telemetry, and measure containment without making ordinary
runtime execution dangerous or nondeterministic.

## Decision

Add strict `FaultScenario` and `FaultPlan` models plus a thread-safe controller.
Plans are disabled by default, require explicit CLI `--execute` arming, and cap
each scenario by an integer injection count and maximum configured delay.

Inject faults through decorators around existing protocols:

- inference generation for timeout, invalid output, context overflow, and OOM;
- tool execution for timeout, result corruption, and malformed arguments;
- terminal result persistence for a controlled database failure;
- a subprocess harness at the committed `recovery_ready` checkpoint for an
  actual worker termination and restart.

Each activation records a `fault.injected` metric containing scenario, point,
occurrence, task, timestamp, and delay. Existing task states, traces, recovery,
and observability remain authoritative. SQLite schema v2 is unchanged.

## Alternatives considered

- Random probabilistic faults: rejected for acceptance evidence because runs
  would not be reproducible and could activate more faults than intended.
- Fault branches embedded throughout `AgentRuntime`: rejected because they mix
  experimental behavior into core orchestration and weaken component boundaries.
- Test-only monkeypatching: rejected because it cannot provide a reusable,
  inspectable runtime capability or CLI report.
- External chaos infrastructure: rejected because this is a local, process-level
  modular runtime with no deployed service mesh or distributed cluster.
- Automatically retry every injected failure: rejected because model/tool
  side-effect boundaries are unsafe without idempotency. Only the existing
  pre-invocation checkpoint is recovered.

## Consequences

- Normal Stage 13 runtime composition is inert unless explicitly armed.
- The same fault adapter can wrap deterministic or real components, while the
  retained suite uses stubs and zero real model calls for safety/reproducibility.
- Negative added latency is valid: most injected faults fail before a successful
  baseline completes. It is not interpreted as a performance improvement.
- The database-result fault reproduced the known completed-state/missing-output
  atomicity gap. The report marks that scenario detected but not contained,
  yielding 8/9 containment rather than claiming perfection.
- Fault injection is reliability testing, not the Stage 14 adversarial security
  suite and not proof of production fault tolerance.

## Evidence

- `tests/test_fault_injection.py` verifies safety arming, validation, exact state
  mapping, count bounds, metrics, corruption, the database gap, factory
  composition, JSON output, and real process termination/recovery.
- `benchmarks/results/stage13-chaos-20260824T193424Z.json` retains the complete
  nine-scenario run.
- `docs/stages/stage13-fault-injection-chaos-framework.md` records measurements
  and limits.
