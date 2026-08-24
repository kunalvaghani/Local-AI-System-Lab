# Stage 4 — Explicit State Machine

## What this stage is for

Stage 3 could report a current task state. Stage 4 makes the path to that state
provable: a task can change state only through one validated graph, and every
accepted change is retained with sequence, reason, and time.

The normal real-agent execution is now:

```text
CREATED -> PLANNING -> EXECUTING -> VALIDATING -> COMPLETED
```

## Component upgrade map

| Component | Before Stage 4 | Stage 4 responsibility |
| --- | --- | --- |
| `TaskState` | Five coarse states | Six execution states plus eight specific terminal failure states |
| `StateTransition` | Missing | Immutable sequence/from/to/reason/timestamp evidence |
| `ExecutionStateMachine` | Direct state dictionary | Owns initialization, legal graph, current state, history, and terminal checks |
| `RuntimeComponents` | No state-machine boundary | Receives a replaceable `TaskStateMachine` dependency |
| `AgentRuntime` | Assigned state directly | Requests validated transitions at planning, invocation, validation, completion, and failure |
| Checkpoints | Broad phase names | One checkpoint for every accepted transition |
| Lifecycle events | Events included a current label | `task.state.changed` includes exact transition provenance |
| Task result | Final state only | Contains the complete ordered state history |
| Native backend | Generic nonzero-exit error | Classifies OOM and context failures into typed errors |
| Output handling | Accepted any text result | Empty/whitespace model output becomes `INVALID_OUTPUT` |
| Error handling | Generic failed/denied states | Maps typed errors to the relevant terminal state |
| Agent CLI | Printed final state and lifecycle events | Also prints the concise per-task transition history |

## Legal graph

| From | Allowed destinations |
| --- | --- |
| `CREATED` | `PLANNING`, `CANCELLED` |
| `PLANNING` | `WAITING_FOR_TOOL`, `EXECUTING`, and relevant terminal failures |
| `WAITING_FOR_TOOL` | `PLANNING`, `EXECUTING`, `TOOL_FAILED`, `TIMEOUT`, `INVALID_OUTPUT`, `SECURITY_BLOCKED`, `CANCELLED` |
| `EXECUTING` | `VALIDATING`, `MODEL_FAILED`, `TIMEOUT`, `OUT_OF_MEMORY`, `CONTEXT_OVERFLOW`, `CANCELLED` |
| `VALIDATING` | `COMPLETED`, `INVALID_OUTPUT`, `TIMEOUT`, `CANCELLED` |
| Any terminal state | None |

Tool waiting/failure are modeled for lifecycle completeness but no tool can be
resolved or executed before Stage 5. Timeout is a typed terminal outcome; the
scheduler does not yet enforce a deadline.

## Demonstrated output

```powershell
python -m runtime.agent_cli --agent technical-explainer
```

The real Qwen task completed with this exact state series:

| Sequence | From | To | Reason |
| ---: | --- | --- | --- |
| 0 | — | `created` | Runtime created the task |
| 1 | `created` | `planning` | Runtime began planning execution |
| 2 | `planning` | `executing` | Qwen route selected |
| 3 | `executing` | `validating` | Model invocation returned a result |
| 4 | `validating` | `completed` | Validated output accepted |

The run generated the same bounded Technical Explainer output as Stage 3 and
observed 1,825.54 ms total time, 1,281.54 ms TTFT, 113.37 tokens/second,
1,339.04 MiB peak process RAM, and a 1,219 MiB VRAM delta. This is a capability
observation, not a new performance baseline.

An attempted direct `CREATED -> COMPLETED` transition is rejected with code
`illegal_state_transition` and structured `current_state`, `requested_state`,
and `allowed_states` details. Tests also prove that every terminal failure state
rejects re-entry.
