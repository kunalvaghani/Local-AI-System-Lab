# ADR-0004: Registered agents and explicit lifecycle events

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 2 proved direct local model inference. Stage 3 requires specialized agents
to execute through the runtime rather than call that backend directly. Agent
identity, role instructions, task ownership, coarse state, lifecycle evidence,
result handling, and failures must remain inspectable without prematurely
implementing Stage 4's formal transition machine or Stage 5's tool executor.

## Decision

Add a runtime-owned `AgentRegistry`, append-only `LifecycleEventStore`, and
`AgentRuntime.run(agent_id, objective)` entry point. A registered `Agent`
contains a stable identity, default objective, system prompt, behavioral
capabilities, and typed tool-capability metadata. Tool declarations grant no
permission and cannot execute anything.

Track only five coarse Stage 3 task states: `created`, `running`, `completed`,
`failed`, and `denied`. The runtime owns task creation, rejects foreign tasks,
passes the selected agent's system prompt into the existing inference
abstraction, packages a typed result, and emits agent/task/model lifecycle
events separately from performance telemetry.

## Alternatives considered

| Alternative | Result | Reason |
| --- | --- | --- |
| Let each agent call llama.cpp | Rejected | Bypasses policy, routing, task identity, lifecycle evidence, and result handling |
| Encode agent roles only in CLI prompts | Rejected | Identity and specialization would not be runtime data |
| Implement the complete state machine now | Deferred to Stage 4 | Legal transition validation and detailed failure states are the next explicit stage |
| Implement callable tools now | Deferred to Stage 5 | Stage 3 needs capability metadata, not host permissions or execution |
| Registry plus runtime-owned `run` | Selected | Creates one inspectable path from agent identity to local result |

## Consequences

- Two specialized agents share one owned execution path and backend contract.
- Agent prompts and declared future tool needs are inspectable data.
- Lifecycle evidence is task/agent scoped and timestamped.
- The runtime remains synchronous and process-local.
- Coarse state assignment is not yet a validated transition machine.
- Small-model role adherence still depends on carefully bounded prompts.

## Evidence

- [`../../runtime/agents.py`](../../runtime/agents.py)
- [`../../runtime/engine.py`](../../runtime/engine.py)
- [`../stages/stage3-agent-runtime-mvp.md`](../stages/stage3-agent-runtime-mvp.md)
- [`../../tests/test_agent_runtime.py`](../../tests/test_agent_runtime.py)
