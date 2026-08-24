# ADR-0007: Bounded aged-priority request scheduler

- Status: Accepted
- Date: 2026-08-24

## Context

The runtime previously invoked inference immediately on the caller thread. It
could neither compare ordering policies nor bound accepted concurrency, expose
queue latency, cancel queued work, or enforce an end-to-end request deadline.
The current llama.cpp adapter deliberately supports one active process.

## Decision

Add a standard-library, process-local worker scheduler with selectable FIFO and
priority policies. The serious real-runtime composition uses priority and one
worker. Requests declare interactive, standard, or background workload classes;
callers may override their numeric priority.

Priority selection is stable for equal values. Wait-time aging increases the
effective priority, and the oldest request beyond a maximum-wait threshold is
promoted before newer work. A queue monitor expires or cancels queued requests
even while all workers are busy. End-to-end deadlines include queue wait and
execution. Active operations receive cooperative cancellation tokens.

Expose immutable request snapshots and aggregate queue metrics: depth, running
count, peak depth, outcomes, P50/P95/max queue wait, starvation promotions, and
execution order. Keep FIFO as a measured baseline rather than assuming priority
is universally better.

## Consequences

- Multiple callers can submit concurrently and observe controlled order.
- The one-worker real composition respects the backend's current concurrency limit.
- Interactive work normally overtakes queued background work without making old
  background work indefinitely ineligible.
- Agent results include queue evidence and scheduler lifecycle events.
- Python cannot forcibly terminate a non-cooperative operation thread. Current
  inference and tests cooperate; stronger process isolation remains future hardening.
- Queue state and metrics disappear on restart until Stage 10 persistence.

## Alternatives considered

- Keep immediate inline execution: rejected because it cannot demonstrate Stage 6 behavior.
- Use only FIFO: retained as baseline but insufficient for interactive latency control.
- Use strict priority without aging: rejected because background starvation is predictable.
- Introduce asyncio or a third-party queue: rejected because current work is blocking/native and standard-library threads keep mechanics inspectable.
- Run several real inference workers: rejected until hardware admission evidence supports it.
