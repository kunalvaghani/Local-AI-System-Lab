# Stage 3 — Agent Runtime MVP

## What this stage is for

Stage 2 proved that the machine can run a real local model. Stage 3 makes that
model a component inside an agent runtime: callers select an agent identity and
objective, while the runtime owns task creation, policy, routing, invocation,
result packaging, state, events, and errors.

The new demonstrable boundary is:

```text
caller -> registered agent -> runtime.run -> owned task -> policy -> route
       -> inference backend -> typed result + lifecycle evidence
```

## Component upgrade map

| Component | Before Stage 3 | Stage 3 responsibility |
| --- | --- | --- |
| `Agent` | Basic identity/objective data | Adds specialized system prompt and typed, declaration-only tool capability metadata |
| `AgentRegistry` | Missing | Owns stable agent definitions; rejects missing and duplicate identities |
| `AgentRuntime` | Caller manually created/executed a task | `run()` owns lookup, task creation, policy, routing, model invocation, and result handling |
| Task state | Checkpoint phase strings only | Exposes coarse `created`, `running`, `completed`, `failed`, or `denied` state |
| Lifecycle events | Lifecycle names were mixed into metric events | Adds timestamped, agent/task-scoped event records while retaining metrics |
| Inference request | Objective and model ID | Also carries the selected specialized agent's system prompt |
| Result | Model output/backend metadata | Adds agent identity, objective, final state, behavioral/tool metadata, and inference measurements |
| Errors | General runtime/component errors | Adds structured missing-agent, duplicate-agent, and foreign-task errors |
| Composition root | Stub runtime and direct real-inference CLI | Adds a real Stage 3 runtime with two pre-registered agents and the Stage 2 backend |
| Agent CLI | Missing | Executes one or both agents through the runtime and prints results plus lifecycle evidence |

Tool capability entries are metadata only. They do not resolve, authorize, or
run tools; that boundary remains Stage 5. The five coarse states are direct
assignments, not a legal-transition engine; that boundary remains Stage 4.

## Specialized agents demonstrated

| Agent | Purpose | Declared future tool capability |
| --- | --- | --- |
| Technical Explainer | Explain local-AI mechanics accurately and concisely | `project_context_read` |
| Runtime Risk Analyst | Identify constrained-device inference risks and mitigations | `risk_register_read` |

Reproduce both real executions:

```powershell
python -m runtime.agent_cli
```

Final verified outputs on 2026-08-24:

> Local inference keeps sensitive data on the device, enhancing privacy.
> Lifecycle events record each step, making the runtime's behavior observable.

> The principal risk is GPU out-of-memory. Mitigation: use a smaller quantized
> model or reduce the context length.

Both tasks finished in `completed` state through `llama.cpp-completion`. Each
emitted `task.created`, `task.started`, `policy.evaluated`, `route.selected`,
`model.invocation.started`, `model.invocation.completed`, and `task.completed`.

| Agent | Total time | TTFT | Generation throughput | Peak RAM | VRAM delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Technical Explainer | 1,823.14 ms | 1,286.15 ms | 114.90 tok/s | 1,339.04 MiB | 1,219 MiB |
| Runtime Risk Analyst | 1,804.23 ms | 1,215.72 ms | 112.16 tok/s | 1,339.15 MiB | 1,215 MiB |

These are capability-run observations, not a replacement for the Stage 2
benchmark distribution.

## Failed prompt experiment retained

An intermediate prompt-bounding attempt completed mechanically but produced
two quality defects: the explainer said local inference “reduces privacy,” and
the risk agent drifted into model training and dataset quality. The system
prompts were then made role-specific, explicitly bounded, and re-run. This is
evidence that task completion and role correctness are separate concerns; a
formal output validator remains future work.
