# ADR-0025 — Container-aware, accessible, bounded rendering

- Status: Accepted
- Date: 2026-08-26
- Stage: 25

## Context

The Stage 24 workbench is a resizable split application, so viewport breakpoints
alone do not describe the width available to the Runtime task grid. Its smallest
text token also measured 4.26–4.42:1 on common dark surfaces, the collapsed
mobile command trigger lost its descriptive name, lifecycle SSE events committed
one React update per event, and hash-only skip focus differed by environment.

The existing trace explorer already bounds a 10,000-step response to 100 DOM
rows per page. The existing React Aria, semantic DOM, and native resizable panel
contracts remain appropriate; none of the measured failures requires a new UI,
virtualization, motion, or chart dependency.

## Decision

Use an inline-size container for Runtime task-grid reflow, remove the global
320 px body floor, and keep mobile route overflow inside one discoverable
horizontal navigation rail. Preserve the accessible resizable split.

Give the command trigger a stable explicit name, restore its focus after palette
dismissal, explicitly focus the main workspace from the skip link, expose API
connection changes as one polite atomic status, and mark the parallel Runtime
query region busy while it is loading. Raise only the failing faint-text token
until it clears 4.5:1 on both canvas and panel surfaces.

Queue lifecycle SSE events and commit them once per animation frame. Flush task
snapshots and stream-end events immediately, preserve event-key deduplication,
and keep the existing 200 retained/30 rendered bounds. Keep deferred trace
filtering and 100-row paging rather than adding another rendering engine.

## Consequences

- Reflow follows the actual resizable workspace width and passes the five-size
  browser matrix without page-level horizontal overflow.
- Stable names, explicit focus paths, live/busy boundaries, and passing token
  contrast improve operability without claiming formal WCAG conformance.
- A 500-event burst causes one scheduled visual commit instead of 500 commits;
  terminal/task reconciliation is still immediate.
- The build grows only 282 gzip JavaScript bytes from Stage 24 and remains below
  the 250 KiB gate; no new dependency is added.
- Client paging still follows a full trace transfer, and manual assistive-
  technology coverage remains a release boundary.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| More viewport media queries | Rejected | A resizable panel can be narrow inside a wide viewport; container width is the relevant signal |
| Set a wider global minimum width | Rejected | It creates page-level horizontal scrolling at 320 px |
| Replace the split on mobile | Rejected | The current vertical accessible split remains usable and keyboard-resizable |
| Add a virtualizer | Rejected | The 10,000-step fixture already renders a bounded 100 rows |
| Update React state for every SSE event | Rejected | Synchronous bursts create avoidable render pressure |
| Announce every lifecycle event | Rejected | A live event rail would overwhelm assistive technology during bursts |
| Add route-level code splitting now | Deferred | The compressed shell passes at 150,118/256,000 bytes; the pre-compression warning alone does not prove a user-facing bottleneck |

## Evidence

- `apps/web/src/App.test.tsx`
- `apps/web/scripts/stage25-smoke.mjs`
- `benchmarks/results/stage25-responsive-accessibility-performance-20260826T182119Z.json`
- `docs/stages/stage25-responsive-accessibility-performance-pass.md`
