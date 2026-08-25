# ADR-0020: Task-scoped agent and scheduler projections

- Status: Accepted
- Date: 2026-08-25
- Stage: 20

## Context

Stage 19 exposes live runtime evidence, but operators still have to correlate
agent identity, lifecycle state, resource admission, and scheduler placement by
reading separate payloads and logs. Stage 20 needs a visual explanation of work
movement without creating a second source of truth or implying a task-history
API that does not exist.

The live scheduler endpoint is a process snapshot and may omit a completed
request. A terminal task retains its authoritative scheduler request and state
history in result metadata. Stub execution legitimately has no admission
decision.

## Decision

Build dependency-free, accessible CSS and semantic HTML projections for
`/agents` and `/scheduler`:

- preserve the validated selected task ID across top-level route navigation;
- use terminal `state_history`, or bounded live SSE states while a task runs;
- show an explicit five-step task/agent/admission/scheduler/outcome handoff;
- sort queued requests only by the scheduler's reported policy, effective
  priority, and stable sequence;
- use the live request when present and retained task metadata after eviction;
- show missing admission and request history as unavailable, never inferred;
- bound the on-screen request ledger to the latest 50 reported requests;
- reuse the real cooperative cancellation mutation.

## Alternatives

### Add a graph-rendering dependency

Rejected for this bounded state path. Native ordered lists and CSS preserve a
complete text equivalent and keep the initial bundle below its existing limit.

### Reconstruct a global task and scheduler history in the browser

Rejected. The API has no list-task contract and the live scheduler snapshot is
not durable history.

### Treat absent stub admission as acceptance

Rejected. `null` is displayed as not reported because no decision exists.

## Consequences

- Operators can follow one URL-selected execution across Runtime, Agents, and
  Scheduler without relying on raw logs.
- Completed tasks remain explainable after scheduler snapshot eviction.
- The interface provides semantic list/table equivalents and adds no graph,
  chart, router, motion, or persistence dependency.
- Global task browsing, trace replay, and high-volume virtualization remain
  outside Stage 20.
