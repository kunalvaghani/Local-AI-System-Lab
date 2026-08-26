# ADR-0024 — Native progressive interaction layer

- Status: Accepted
- Date: 2026-08-26
- Stage: 24

## Context

The workbench has twelve shallow routes, one resizable workspace/evidence split,
live status changes, and dense specialist views. Stage 17 recommended native
CSS/View Transitions first, React Aria for command behavior, and animation
dependencies only after measured need. Stage 21 already bounds a 10,000-step
trace fixture to 100 rendered rows, so interaction polish does not imply a new
virtualization or rendering engine.

## Decision

Use React Aria's existing modal, search, and ListBox behavior for one global
command palette. Preserve native links and the owned History API adapter. When
the stable browser `document.startViewTransition` API exists and reduced motion
is not requested, wrap only the route commit and name three small orientation
surfaces: route heading, active rail item, and contextual evidence. Otherwise
commit immediately.

Keep motion at the existing 120/180 ms tokens and use it only for entry, press,
route orientation, or one-shot status feedback. Extend the evidence pane with
route/task/source facts, progressive interaction guidance, and a reset for the
existing split. Do not add Motion, cmdk, springs, animated numbers, arbitrary
docking, canvas, WebGL, or another virtualizer.

## Consequences

- Keyboard users have a focus-managed, filterable path to every route.
- Unsupported browsers and reduced-motion users receive the same navigation and
  state update without waiting for animation.
- The palette activates more of React Aria and adds 19,160 gzip JavaScript bytes,
  while the 149,836-byte build remains below the 256,000-byte gate.
- Real-browser motion, interaction latency, screen-reader, contrast, reflow, and
  breakpoint evidence remains Stage 25 work; jsdom tests are not conformance.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Motion/Framer Motion | Rejected | Native transitions satisfy the demonstrated cases without runtime state or bundle cost |
| cmdk | Rejected | Overlaps installed React Aria behavior and adds another interaction contract |
| React canary ViewTransition components | Rejected | Stable React/browser APIs are the project baseline |
| Animate the whole workspace snapshot | Rejected | Dense trace/performance surfaces would increase paint and memory cost |
| Arbitrary pane docking | Rejected | No demonstrated workflow offsets focus, persistence, and responsive complexity |
| Canvas/WebGL navigation or charts | Rejected | Current semantic DOM views remain bounded and provide direct text access |

## Evidence

- `apps/web/src/App.test.tsx`
- `apps/web/scripts/stage24-smoke.mjs`
- `benchmarks/results/stage24-interaction-motion-20260826T155934Z.json`
- `docs/stages/stage24-advanced-interaction-motion-polish.md`
