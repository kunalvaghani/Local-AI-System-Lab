# Systems Design: Scheduling, Routing, Persistence, and Recovery

## Runtime ownership

`AgentRuntime` coordinates explicit protocols rather than delegating core logic
to an agent framework. A task owns identity, objective, state, lifecycle events,
model/tool evidence, compute budget, and result. Legal transitions are validated;
failure types map to distinct terminal states instead of one generic exception.

## Scheduler design

The scheduler is a bounded worker queue with selectable FIFO or stable priority
ordering. Interactive, standard, and background workloads carry explicit
priority; equal priority preserves submission order. Wait-time aging and an
oldest-request maximum-wait promotion address starvation while an independent
queue monitor expires or cancels queued work even when workers are occupied.

Deadlines cover queue wait plus execution. Cancellation is cooperative for
running inference, and queue/execution metrics retain depth, wait distribution,
execution order, outcome, and promotions. The current real backend uses one
worker because one llama.cpp process fits the measured 4 GB GPU boundary; adding
workers without memory evidence would turn concurrency into OOM risk.

Alternatives rejected: an unbounded executor hides pressure; preemptive thread
termination is unsafe in Python; microservice queues add operations before the
single-host workload justifies them. Evidence is in the [Stage 6 report](../stages/stage6-request-scheduler.md).

## Model routing and compute budgets

The registry records model identity, artifact/backend availability, capability
metadata, workload fit, benchmark profile, and compute budget. Routing first
filters unavailable candidates, scores workload/policy fit, explains candidates
and rejection, then selects an adaptive inference profile and re-runs exact
memory admission before scheduling.

Budgets bound model calls, generated tokens, time, and estimated RAM/VRAM where
enforceable. Only Qwen2.5 1.5B has a real installed backend, so controlled route
differences demonstrate policy mechanics, not two-model quality superiority.
Evidence is in the [Stage 9 report](../stages/stage9-model-registry-router-budgets.md).

## Memory admission

The profiler reports source and confidence for CPU, RAM, GPU, and VRAM. A
model/profile estimator applies explicit reserves and produces `ACCEPT`, `QUEUE`,
`REDUCE_CONTEXT`, `REDUCE_GPU_OFFLOAD`, `FALLBACK`, or `REJECT_UNSAFE`. Unknown
RAM fails closed; missing GPU may recommend CPU only when policy permits.
Predictions are compared with measured usage and remain estimates, not guarantees.

## Persistence model

SQLite schema v2 stores tasks, agents, state transitions, checkpoints, model
configuration, tool calls, outputs, lifecycle/metric events, trace runs/steps,
and replay reports. WAL plus FULL synchronous mode and short transactions fit a
single-host inspectable runtime. State reconstruction rejects illegal history and
newer unknown schema versions; v1 migration is idempotent.

## Recovery semantics

Recovery is allowed only from an explicit pre-invocation `recovery_ready`
checkpoint. A killed worker is reconstructed, enters `recovering`, and is
resubmitted through current routing, admission, and scheduler policy. Native
token generation and arbitrary model/tool side effects are never resumed because
the runtime lacks universal idempotency guarantees.

Terminal state and output are currently adjacent transactions. A crash between
them can leave `completed` without output; chaos reproduces this and labels it
uncontained. The system chooses visible manual repair over unsafe duplicate side
effects. Evidence is in the [Stage 10 report](../stages/stage10-persistence-checkpoints-recovery.md)
and [Stage 13 report](../stages/stage13-fault-injection-chaos-framework.md).

## Concurrency and scaling boundary

Scheduler queues, API in-flight ownership, SSE cursors, and active workers are
process-local. SQLite is not distributed coordination. The design is a modular
monolith because it keeps causality inspectable on one constrained workstation;
service extraction requires measured independent scaling or isolation needs.
