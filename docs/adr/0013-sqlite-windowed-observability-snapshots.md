# ADR-0013 — SQLite Windowed Observability Snapshots

- Status: Accepted
- Date: 2026-08-24

## Context

Stages 6–11 already produce useful scheduler, inference, hardware, routing,
failure, recovery, and trace evidence. The evidence is split between durable
SQLite records, output payloads, and process-local snapshot providers. Stage 12
needs one inspectable backend report without adding an external telemetry stack,
inventing unavailable samples, or building the future API/frontend.

## Decision

Add a standard-library `UnifiedObservabilityBackend` behind a narrow protocol.
It reads a consistent, windowed SQLite transaction through a dedicated source
adapter, calculates explicit sample distributions, and optionally attaches live
scheduler and hardware snapshots.

The report contract contains:

- task-state and activity totals;
- count/min/P50/P95/max/mean distributions with units;
- recent task and lifecycle-event drill-down;
- current scheduler and source-labelled hardware snapshots;
- a source map and warnings for unavailable live evidence.

Unavailable measurements use a zero sample count and `null` statistics. The
`retries` total is explicitly defined as durable recovery attempts because the
runtime has no independent generic retry subsystem. SQLite schema v2 remains
unchanged because Stage 12 queries existing durable records rather than adding
new canonical execution data.

## Alternatives considered

- OpenTelemetry plus an external collector: deferred because it adds services,
  dependencies, export policy, and deployment work that the current local
  single-host runtime does not require.
- A metrics-only table populated on every operation: rejected for this stage
  because it duplicates authoritative durable records and adds write-path cost.
- Reading only process-local collectors: rejected because restart and recent
  task inspection require durable evidence.
- A GUI dashboard: deferred to the approved frontend stages; Stage 12 owns only
  the backend and machine-readable CLI surface.

## Consequences

- One report now correlates execution, model, tool, route, scheduler, failure,
  recovery, trace, and resource evidence.
- Existing-database reporting does not start the runtime or append lifecycle
  events to the database it is observing.
- Collection is local and pull-based; it adds no background sampler or network.
- Recent-task detail uses bounded follow-up queries and is suitable for the
  configured local limit, not an unbounded analytics workload.
- Live scheduler state belongs to the reporting process. Historical scheduler
  timing comes from SQLite and remains distinct.
- Retention, redaction, authenticated export, remote collection, and the public
  API remain future work.

## Evidence

- `tests/test_observability.py` covers aggregation, exact percentiles, windows,
  bounded drill-down, missing values, live evidence, composition, and CLI JSON.
- `benchmarks/run_stage12_observability.py` retains a controlled report.
- `docs/stages/stage12-observability-metrics-backend.md` records measurements
  and stage boundaries.
