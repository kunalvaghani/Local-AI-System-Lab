# Stage 25 — Responsive, Accessibility & Performance Pass

## Stage Completed

Stage 25 hardens the local Systems Cartography workbench for realistic viewport,
keyboard, assistive-semantic, data-volume, streaming, and slow-response
conditions. It is for keeping the existing interface usable under pressure, not
for adding a new product feature. It stops before Stage 26 end-to-end product
verification.

## What This Stage Is For

- Verify the full shell at desktop, tablet, narrow, mobile, and 320 px widths.
- Make every critical navigation and resize path keyboard-operable with visible
  focus and deterministic focus return.
- Validate semantic landmarks, accessible names, live status boundaries,
  reduced motion, and computed color contrast without claiming certification.
- Bound browser work for long traces and high-frequency event streams.
- Preserve honest loading and disabled states during slow backend responses.
- Measure the built shell and local route/API retrieval where that evidence is useful.

## Component Upgrades

| Component | What it does | Stage 25 upgrade |
| --- | --- | --- |
| Responsive shell | Composes system bar, route rail, workspace, splitter, and evidence pane | Removes the fixed 320 px body floor, verifies reflow at five viewports, and keeps the only horizontal overflow inside the intentional mobile route rail |
| Runtime command center | Shows API health, capacity, models, tasks, telemetry, and execution evidence | Uses a named inline-size container so the task composer/inspector stack according to actual panel width rather than viewport width |
| Command trigger/palette | Provides global route navigation | Keeps the accessible name `Navigate workspaces` when the visible label collapses and explicitly restores focus after Escape/dismissal |
| Skip link | Bypasses repeated shell navigation | Explicitly focuses the `main` workspace instead of relying on inconsistent hash-focus behavior |
| Connection status | Announces loopback API availability | Becomes a polite, atomic status region while lifecycle event lists remain non-live to avoid announcement floods |
| Runtime loading boundary | Coordinates six parallel inspection queries | Exposes `aria-busy` and retains truthful loading copy and disabled controls during delayed responses |
| Task composer | Creates one bounded runtime task | Separates backend-data loading from mutation submission so a slow initial load says `Launch task`, not the false `Submitting…` |
| Design tokens | Defines text, surface, state, and focus colors | Raises faint text from failing 4.26–4.42:1 combinations to 4.81–4.99:1 while every measured text pair meets its threshold |
| SSE task hook | Reconciles selected-task lifecycle/task/end events | Batches lifecycle bursts once per animation frame, flushes task/end events immediately, deduplicates, and retains at most 200 events |
| Trace explorer | Filters and inspects redacted trace steps | Retains deferred filtering and 100-row pages; a 10,000-step fixture still renders only 100 list rows |
| Validation runner | Checks served routes, tokens, bundle, source contracts, and backend health | Adds a twelve-route Stage 25 smoke with calculated contrast ratios, reflow/reduced-motion contracts, stream batching/bounds, gzip budget, and retained JSON evidence |

## Browser Verification

The local runtime was inspected in the in-app Chromium browser at 1440×900,
1024×768, 768×1024, 390×844, and 320×568. After responsive layout settling,
body and document scroll widths matched their client widths at every size. On
mobile, the grouped route rail remains intentionally horizontally scrollable and
all page content remains within the viewport.

The browser accessibility snapshot exposed a skip link, banner, named
application navigation, one main landmark, the named Runtime pulse region,
labelled controls and meters, one keyboard separator, a polite status, and a
named complementary evidence region. The command search receives focus on open;
Escape returns focus to the named trigger with a solid visible outline. The
splitter changed from 76% to 71% through `ArrowLeft`.

This is strong implementation evidence, not a WCAG conformance report. No claim
is made for NVDA/JAWS/VoiceOver compatibility or every browser/OS combination.

## Stress and Performance Evidence

- A 500-event synchronous SSE burst schedules one render frame, then keeps 200
  events in client memory and renders the newest 30 lifecycle rows.
- A 10,000-step trace renders 100 rows per page and preserves deterministic paging.
- Delaying every mocked backend response keeps explicit connecting/loading
  states, `aria-busy`, and disabled task controls until data resolves.
- All twelve workbench routes returned HTTP 200 in 30.933–56.046 ms in the final
  one-run local smoke; median retrieval was 37.401 ms.
- Loopback health returned in 34.123 ms with runtime `running` and SQLite
  integrity `ok`.
- The final build contains one 150,118-byte gzip JavaScript asset, 58.6% of the
  256,000-byte gate, plus 9.43 KiB gzip CSS.
- The single pre-compression JavaScript chunk remains above Vite's 500 kB warning
  threshold. The gzip gate passes, so route splitting stays a measured follow-up
  rather than an unproven Stage 25 rewrite.

## Tests Performed

- 38/38 Vitest/Testing Library/axe component tests passed.
- Added explicit accessible-name/focus-return, skip-link focus, 500-event frame
  batching/200-event retention, and slow-backend pending-state tests.
- Retained reduced-motion bypass, open-palette and eight-route axe scans,
  keyboard navigation, splitter semantics, and all specialist-route regressions.
- Production TypeScript/Vite build passed.
- 250 KiB compressed JavaScript gate passed at 150,118 bytes.
- Twelve-route/health/contrast/reflow/stream-contract Stage 25 smoke passed and
  retained `stage25-responsive-accessibility-performance-20260826T182119Z.json`.
- Real-browser viewport, accessible-tree, focus, command dismissal, and keyboard
  splitter checks passed.

## Files Added

- `apps/web/scripts/stage25-smoke.mjs`
- `benchmarks/results/stage25-responsive-accessibility-performance-20260826T182119Z.json`
- `docs/adr/0025-container-aware-accessible-bounded-rendering.md`
- `docs/stages/stage25-responsive-accessibility-performance-pass.md`

## Files Modified

- App shell, system bar, runtime command center/composer, route workspace, SSE
  event hook, token/global/runtime styles, frontend tests, package identity, and
  validation commands.
- Project state, README, architecture, development, repository, ADR index, and
  risk documentation.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| Viewports | Usable across realistic sizes | Five-size browser matrix passed; only the intentional mobile route rail scrolls horizontally |
| Keyboard/focus | Complete primary operation with visible focus | Skip, command open/dismiss, navigation, and splitter paths are explicit and tested |
| Reduced motion | Same capability without unnecessary motion | Native transition bypass and near-zero CSS durations remain tested |
| Screen-reader semantics | Relevant structure and names exposed | Browser accessibility tree and axe scans expose named landmarks, controls, meters, status, and evidence boundaries |
| Contrast | Readable semantic text/focus | Nine token pairs pass their 4.5:1 text or 3:1 focus threshold; faint text is now 4.81:1 minimum |
| Large data/long traces | Bounded rendering | 10,000 steps remain 100 rows per page |
| Streaming updates | Avoid rerender storms | 500 lifecycle events coalesce into one frame; 200 retained/30 rendered |
| Slow backend | Honest usable pending state | Loading, `aria-busy`, disabled actions, and accurate button language persist until resolution |
| Performance | Useful measured evidence | Build/bundle gate and twelve-route/health timings retained without overstating lab timings |

## Remaining Boundaries

- Accessibility automation and one Chromium accessibility snapshot are not
  certification and do not replace human assistive-technology review.
- The selected trace API still transfers the full trace before client paging;
  server pagination remains the next response if measured traces outgrow the
  current local contract.
- The Vite development timing sample is a one-run local measurement, not a field
  Core Web Vitals claim.
- Route-level code splitting is still a candidate because the minified chunk is
  513.55 kB before compression; no user-visible or gzip-budget failure justified
  expanding Stage 25 into an architecture rewrite.

## Next Stage

Stage 26 — End-to-End Product Verification. No Stage 26 implementation was started.
