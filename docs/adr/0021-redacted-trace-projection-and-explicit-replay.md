# ADR-0021: Redacted trace projection and explicit replay

- Status: Accepted
- Date: 2026-08-25
- Stage: 21

## Context

The Stage 11 backend already records ordered, hash-chained trace steps and can
replay deterministic reducers without repeating nondeterministic or
side-effecting work. Stage 15 exposes a safe projection that intentionally
omits raw input/output payloads, run metadata, and detailed failures. Operators
still need a visual way to debug one selected run without weakening those
boundaries or implying a cross-run comparison endpoint that does not exist.

Recorded timestamps identify when steps were written, but do not establish the
exclusive execution duration of each component. Large traces also require a
bounded rendered DOM even when the current API returns the complete run.

## Decision

Implement `/traces` as a local, task-scoped Trace Explorer and Replay Debugger:

- retrieve only `GET /v1/tasks/{task_id}/trace` safe projections;
- preserve the validated task ID and one optional validated `?step=` expansion
  in URL state while keeping filters, search, replay result, and paging ephemeral;
- present recorded order, state/model/tool classification, determinism,
  actor/component identity, safe failures, hashes, and chain links;
- label timing bars as exact gaps between recorded timestamps, never as
  component execution latency;
- render no more than 100 filtered trace rows per page, defer search, and
  memoize derived lookup maps;
- invoke replay only after an explicit user action;
- show integrity, reconstructed state, aggregate counts, and each backend
  replay outcome/reason; and
- state that cross-run divergence comparison is unavailable until the API
  exposes a bounded comparison contract.

## Alternatives

### Expose raw prompts, outputs, or detailed failures in the browser

Rejected. This would reverse the accepted API redaction boundary and broaden
sensitive-data exposure merely for presentation convenience.

### Automatically replay whenever a trace loads

Rejected. Replay is a deliberate diagnostic action. Automatic mutation would
blur inspection and execution even though the current backend is side-effect-
free by design.

### Present timestamp gaps as latency

Rejected. Consecutive record times include all intervening work and scheduling;
they are evidence of elapsed gaps, not isolated component duration.

### Build cross-run comparison in the browser

Rejected. The accepted API returns a source trace and its replay report, not two
comparable safe runs. Client-derived comparison would create an unsupported
source of truth.

## Consequences

- A previous selected execution can be inspected step by step from a deep link.
- Raw payload redaction and side-effect-free replay semantics remain intact.
- A 10,000-step fixture keeps the rendered timeline at 100 rows without adding
  a graph or virtualization dependency.
- Filters operate over the complete fetched trace, so very large future runs
  may still require server-side pagination or streaming.
- Cross-run divergence, replay breakpoints, and state overrides remain outside
  Stage 21.
