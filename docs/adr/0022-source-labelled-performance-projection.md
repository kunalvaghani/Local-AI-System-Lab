# ADR-0022: Source-labelled performance projection

- Status: Accepted
- Date: 2026-08-25
- Stage: 22

## Context

Stages 7–12 already expose current hardware, scheduler snapshots, registered
model benchmarks and budgets, inference distributions, and bounded recent task
telemetry. Those values are split across API resources and have different
cadences, sources, sample counts, and null semantics. Stage 22 needs one visual
investigation surface without adding a second metrics store or pretending the
pull-based backend is a continuous hardware sampler.

The unified metrics endpoint can optionally perform live hardware and scheduler
probes. The frontend already owns those resources independently, and a hardware
profile can take hundreds of milliseconds. A second probe on every metrics poll
would add avoidable work on the constrained target machine.

## Decision

Implement `/hardware` and `/metrics` as two entry points to one read-only,
source-labelled performance projection:

- retain dedicated hardware, scheduler, model, metric, and selected-task query
  owners with their accepted cadences;
- request durable metrics with `live=false` to avoid duplicate live probes;
- show CPU topology rather than CPU utilization because no percentage exists;
- render RAM/GPU/VRAM meters only when their inputs are measured;
- prefer selected-task TTFT, token rate, and queue delay, then sampled P50, then
  a matching retained model benchmark explicitly labelled as retained;
- never attach one registered model's benchmark to a different selected model;
- show counts, P50, P95, max, units, collection time, source, confidence, and
  warnings beside performance evidence;
- expose exact profile configuration only when selected-task metadata reports it;
- use at most the API's eight recent tasks for comparative duration bars; and
- add no chart, graph, router, browser database, or continuous sampler.

## Alternatives

### Poll unified metrics with `live=true`

Rejected. The page would run the same hardware and scheduler probes once through
metrics and again through their existing query owners.

### Render missing meters at zero

Rejected. Zero is a valid measured GPU/VRAM or latency value and must remain
distinct from unavailable evidence.

### Use the installed model's benchmark for every selected task

Rejected. Stub, future compact, or alternate model executions cannot inherit a
Qwen 1.5B performance baseline merely because that model is registered.

### Add a charting dependency and browser-side time-series store

Rejected. The backend exposes bounded recent tasks, not a continuous sampling
contract. CSS bars and semantic tables are sufficient for the approved evidence.

## Consequences

- Operators can investigate current hardware, inference latency, throughput,
  queue behavior, model availability, configuration, and recent task variation
  without reading raw JSON.
- Performance provenance and missing-sample boundaries remain visible.
- Hardware profiling is not duplicated by the metrics poll.
- Continuous resource history, experiment comparison, and CPU utilization
  charts require future backend contracts.
