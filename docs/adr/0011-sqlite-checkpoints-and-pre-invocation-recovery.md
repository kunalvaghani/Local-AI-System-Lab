# ADR-0011: SQLite durability and pre-invocation recovery

- Status: Accepted
- Date: 2026-08-24

## Context

Stages 3–9 produced task, agent, state, event, tool, route, budget, scheduler,
and output evidence, but every store was process-local. Recovery cannot be safe
unless the runtime defines which checkpoints precede external or model side
effects and refuses ambiguous retries.

## Decision

Use Python's standard-library SQLite adapter with schema version 1, transactional
idempotent migration, foreign keys, a 5-second busy timeout, WAL journaling, and
`FULL` synchronous durability. Persist typed fields plus explicit JSON; never
pickle runtime objects.

The shared database owns narrow adapters for agent lookup, lifecycle events,
metrics, checkpoints, and state history. The existing legal transition graph
remains authoritative. Add `RECOVERING` as an explicit non-terminal state.

Automatic recovery is permitted only when the current state is `PLANNING` and
the latest checkpoint is `recovery_ready` with both model and tool invocation
marked not started. A restart records `PLANNING -> RECOVERING -> PLANNING` and a
recovery-attempt ledger entry before normal execution continues. Terminal tasks
and in-flight `EXECUTING`/tool boundaries are inspectable but never retried.

## Consequences

- Tasks, agents, transitions, checkpoints, lifecycle/metric steps, model
  configuration, tool calls, outputs, timestamps, and recovery attempts survive
  restart.
- Illegal transitions roll back without partially changing task state.
- Completed outputs are not duplicated by automatic recovery.
- Recovery is intentionally at-least-once only for the side-effect-free planning
  boundary; arbitrary mid-token/model/tool continuation is not claimed.
- Database files remain ignored local runtime state; compact recovery evidence is
  retained as JSON.
- Stage 11 can build trace/replay identifiers over durable records rather than
  transient lists.

## Alternatives considered

- Persist Python pickles: rejected for unsafe deserialization and brittle schema evolution.
- Retry every non-terminal task: rejected because model/tool effects could duplicate.
- Resume native llama.cpp mid-generation: rejected because the current subprocess
  backend exposes no trustworthy serializable generation state.
- Introduce PostgreSQL now: rejected because a single-user local runtime does not
  yet justify a service dependency.
