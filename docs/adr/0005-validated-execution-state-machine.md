# ADR-0005: Validated execution state machine

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 3 stored a coarse current state by direct assignment. That showed whether
a task ended, but it could not prove how execution moved, reject skipped work,
or distinguish model, tool, timeout, validation, memory, policy, context, and
cancellation failures. Stage 4 requires a deterministic and inspectable series
of legal transitions without implementing Stage 5 tools or Stage 6 scheduling.

## Decision

Introduce one runtime-owned `ExecutionStateMachine` with a closed legal graph,
ordered `StateTransition` records, terminal-state enforcement, and structured
`IllegalStateTransitionError` details.

The normal agent path is:

```text
CREATED -> PLANNING -> EXECUTING -> VALIDATING -> COMPLETED
```

`WAITING_FOR_TOOL` is represented and can return to planning or continue to
execution, but no tool is called. Terminal variants are `MODEL_FAILED`,
`TOOL_FAILED`, `TIMEOUT`, `INVALID_OUTPUT`, `OUT_OF_MEMORY`,
`SECURITY_BLOCKED`, `CONTEXT_OVERFLOW`, and `CANCELLED`.

Each accepted transition is appended with sequence, source, destination,
reason, and UTC timestamp; it also becomes a checkpoint and lifecycle event.
The runtime maps typed errors to specific terminal states and classifies native
llama.cpp OOM/context failures. The minimal Stage 4 validator rejects empty
model output before completion.

## Alternatives considered

| Alternative | Result | Reason |
| --- | --- | --- |
| Continue assigning a current-state field | Rejected | Cannot reject illegal jumps or reconstruct execution |
| Scatter transition checks through runtime branches | Rejected | Produces inconsistent rules and weak testability |
| Use an external workflow/state-machine framework | Rejected | Core mechanics must remain inspectable and dependency-free |
| Implement retries/timeouts/tools now | Deferred | Those belong to scheduler and tool stages |
| Central validated graph with ordered history | Selected | One auditable rule set serves runtime, tests, events, and results |

## Consequences

- Every task created by the runtime has an immutable ordered state history.
- Terminal states cannot be re-entered or resumed accidentally.
- Illegal transitions disclose current/requested/allowed states as structured data.
- Failure meaning is more precise than a generic failed flag.
- `WAITING_FOR_TOOL` and `TOOL_FAILED` are structural only until Stage 5.
- Timeout state mapping exists, but active timeout enforcement remains future work.
- Output validation is intentionally minimal and does not prove semantic correctness.

## Evidence

- [`../../runtime/state_machine.py`](../../runtime/state_machine.py)
- [`../../runtime/engine.py`](../../runtime/engine.py)
- [`../../tests/test_state_machine.py`](../../tests/test_state_machine.py)
- [`../stages/stage4-explicit-state-machine.md`](../stages/stage4-explicit-state-machine.md)
