# ADR-0019: Real loopback query and SSE client

- Status: Accepted
- Date: 2026-08-25
- Stage: 19

## Context

Stage 18 provides the local Systems Cartography shell but deliberately makes no
runtime request. Stage 19 must turn `/runtime` into a command center using the
accepted Stage 15 API without copying server evidence into browser storage,
inventing unavailable values, or coupling the core runtime to React.

The API exposes independent inspection resources over JSON and one ordered,
task-scoped lifecycle stream over SSE. Tasks may be inspected or cancelled by
ID, while active API ownership remains process-local.

## Decision

Use TanStack Query 5.102.3 as the typed server-state owner and the browser's
native `EventSource` as a small task-lifecycle adapter:

- fetch health, agents, scheduler, hardware, models, and metrics independently;
- poll each resource at a cadence appropriate to its volatility;
- store the selected task ID only in `?task=`, never in `localStorage`;
- keep at most 200 ordered events for the selected task and render the latest 30;
- reconnect a timed-out continuing stream using its explicit event cursor;
- close terminal streams and invalidate the affected query evidence;
- preserve `null`, unavailable models, request IDs, and explicit stub metadata;
- keep all requests relative to the loopback-only Vite `/v1` proxy.

The runtime command center owns launch, inspection, cancellation, lifecycle,
hardware/model, scheduler, and metric evidence. Rich scheduler graphs, trace
replay, hardware experiments, chaos, and security specialist screens remain
later approved stages.

## Alternatives

### Hand-written global fetch cache

Rejected. Deduplication, cancellation, stale state, retries, invalidation, and
polling would become custom infrastructure with little portfolio value.

### WebSocket transport

Rejected. The accepted API is server-to-client lifecycle delivery and already
provides bounded SSE. A bidirectional protocol would add an unjustified backend
path.

### Persist tasks or telemetry in browser storage

Rejected. The backend and SQLite are authoritative. Browser persistence would
create stale alternate evidence and additional sensitive-data retention.

### Simulated UI data while the API is absent

Rejected. Loading, unavailable, and request-specific error states are part of
the product contract and must remain visible.

## Consequences

- `/runtime` is now a real local control surface rather than a shell mockup.
- URL-addressable task inspection survives refresh while active task ownership
  still obeys the backend's documented restart boundary.
- One new production dependency increases initial JavaScript from 102,802 to
  117,956 gzip bytes (+15,154, 14.7%), still below the 256,000-byte gate.
- Polling and SSE overlap intentionally for terminal reconciliation; richer
  event volumes still require Stage 20/21 performance work.
- Automated DOM accessibility checks remain non-certifying and do not replace
  real-browser keyboard, contrast, zoom, forced-color, or screen-reader testing.
