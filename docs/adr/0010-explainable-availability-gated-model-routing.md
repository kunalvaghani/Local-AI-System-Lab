# ADR-0010: Explainable availability-gated model routing and task budgets

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 8 safely adapted one pinned model but the router remained static and the
runtime had no task-level call, token, time, or memory limits. Only one real GGUF
artifact is currently installed. Treating an alias, stub, or missing artifact as
a second available model would make the Stage 9 evidence misleading.

## Decision

Use a typed, versioned registry whose availability requires both a local artifact
and a configured backend. Keep the optional compact candidate visible but
unavailable until both conditions become true. Route from task type, complexity,
context/output length, workload/latency, queue depth, live memory, declared
capabilities, and measured benchmark evidence. Retain every candidate's reasons.

Resolve a typed compute budget per workload, with caller override. Enforce call
count and generated-token caps before invocation, cap the scheduler deadline by
remaining task time, and compare the exact Stage 8 memory estimate with RAM/VRAM
limits before scheduler submission. Record post-execution measurements without
claiming they can retroactively prevent a transient peak.

## Consequences

- Route and budget decisions are inspectable in lifecycle events and results.
- Controlled two-model evaluation proves distinct workload routes without
  claiming that the missing compact GGUF was executed or benchmarked.
- Live routing truthfully selects the single installed/configured model and
  explains why the compact candidate was skipped.
- Current real composition remains one backend/model. Adding a second real model
  requires its artifact, pinned backend configuration, profiles, admission
  metadata, and measurements; registry availability alone cannot bypass these.
- Routing and budget ledgers remain process-local until Stage 10 persistence.

## Alternatives considered

- Count two aliases of one GGUF as two models: rejected as false evidence.
- Silently download a second model: rejected because Stage 9 can be demonstrated
  without expanding the approved artifact/network scope.
- Rely only on llama.cpp native fitting: rejected because it hides policy and
  conflicts with the existing exact-profile `--fit off` boundary.
