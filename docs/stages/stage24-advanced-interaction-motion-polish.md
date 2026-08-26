# Stage 24 — Advanced Interaction & Motion Polish

## Stage Completed

Stage 24 gives the local workbench a keyboard-first navigation layer and a
restrained native motion language. It is for preserving orientation and making
state changes legible, not decorating the interface. It stops before the Stage
25 responsive, accessibility, and performance pass.

## Expected Output

- Reach a distinctive, modern interaction standard without reducing responsiveness.
- Evaluate current browser-native motion, command navigation, contextual panels,
  resizable workspaces, large data, and rendering techniques against real need.
- Require every major animation to explain orientation, hierarchy, causality,
  state change, attention, or feedback.

## Actual Output

| Component | What it does | Stage 24 upgrade |
| --- | --- | --- |
| Command palette | Opens with `Ctrl/Cmd+K` or `/`, traps focus, filters twelve routes, and supports ListBox keyboard action | Makes every workbench route reachable without traversing the rail |
| Native route transition adapter | Wraps shallow History API commits with `document.startViewTransition` when supported | Adds orientation feedback while preserving instant fallback and native links |
| Named transition surfaces | Animates only the route heading, active rail item, and contextual evidence pane | Limits snapshot/paint work and makes route hierarchy changes legible |
| Reduced-motion gate | Bypasses View Transitions and collapses CSS animation duration | Preserves the complete route/state change without spatial interpolation |
| Contextual evidence pane | Shows current domain, route, selected-task scope, endpoint, and request-to-view path | Keeps source and selection context adjacent to every specialist workspace |
| Interaction disclosure | Reveals shortcuts, separator behavior, task retention, and pane reset on demand | Adds guidance without permanently increasing interface density |
| One-shot feedback | Applies brief enter/press/status feedback only when a control or state appears/changes | Communicates causality without loops, pulses, particles, or ambient motion |
| Resizable workspace reset | Restores the accepted 76/24 or stacked 68/32 layout | Retains the existing accessible split while adding a recovery control |

## Technique Evaluation

| Technique | Decision | Evidence |
| --- | --- | --- |
| View Transitions | Adopt as progressive enhancement | Native, zero dependency, bounded to three orientation surfaces |
| Modern CSS transitions/micro-interactions | Adopt | 120/180 ms tokenized, one-shot, and reduced-motion aware |
| Command palette/keyboard-first navigation | Adopt with existing React Aria | Twelve routes need fast access; no overlapping `cmdk` dependency |
| Contextual panels/progressive disclosure | Extend existing evidence pane | Existing split already owns contextual information and resize semantics |
| Resizable/dockable workspaces | Keep one resizable split; reject arbitrary docking | No demonstrated multi-window use case justifies focus/persistence complexity |
| Virtualized data | Defer | The 10,000-step fixture already renders at most 100 rows per page |
| Spring physics/animated numbers | Reject for this stage | No state change requires simulated physics or continuously interpolated values |
| Canvas/WebGL | Reject | Current semantic lists, meters, and CSS bars remain bounded and accessible |
| Animation library | Reject | Native CSS and browser APIs satisfy the demonstrated interaction needs |

## New Demonstrable Capability

An operator can open a modal workspace navigator from anywhere, filter and open
a route by keyboard, retain selected-task context, understand the destination
through a brief native transition when available, inspect the route/source
boundary, and restore the evidence split without adding a motion dependency.

## Files Added

- `apps/web/src/components/interaction/CommandPalette.tsx`
- `apps/web/src/styles/interaction.css`
- `apps/web/scripts/stage24-smoke.mjs`
- `benchmarks/results/stage24-interaction-motion-20260826T155934Z.json`
- `docs/adr/0024-native-progressive-interaction-layer.md`
- `docs/stages/stage24-advanced-interaction-motion-polish.md`

## Files Modified

- App shell, system bar, evidence pane, route adapter, global style composition, and component tests.
- Frontend package/lock identity and validation commands.
- Project state, README, architecture, development, repository, ADR index, and risk documentation.

## Tests Performed

- Command shortcut, filtering, keyboard action, and selected-task route retention.
- Slash-shortcut protection for editable controls.
- Native View Transition invocation and reduced-motion immediate fallback.
- Context disclosure and pane reset availability.
- Open-command-palette axe-core scan and all existing route-specific scans.
- Production TypeScript/Vite build, compressed bundle gate, six-route/API smoke, and diff hygiene.

## Measurements

- Frontend component suite: 34/34 passed; 12.26 seconds test time, 16.32 seconds total runner time.
- Production build: 494 transformed modules; 149,836 gzip JavaScript bytes, 58.5% of the 256,000-byte gate.
- CSS: 58.21 kB built, 9.36 KiB gzip.
- Stage 24 smoke: six routes returned HTTP 200 in 22.357–48.888 ms; median 24.46 ms.
- Loopback health retrieval: 26.329 ms; runtime `running`, persistence integrity `ok`.
- Complete smoke: 58.705 ms. These are one-run local development-server timings, not browser interaction metrics.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| Route orientation | Useful modern transition | Native progressive transition on three small surfaces |
| Keyboard navigation | Fast route access | Global accessible palette for all twelve routes |
| Contextual panels | Preserve hierarchy/source context | Existing evidence pane upgraded with route/task/source facts |
| Resizable workspace | Useful recovery behavior | Existing split retained with explicit reset |
| Large data | Remain responsive | Existing 100-row bound retained; no unjustified virtualizer |
| Motion restraint | No visual noise | No looping motion, animation runtime, particles, spring, canvas, or WebGL |
| Reduced motion | Preserve functionality | View Transition bypass plus near-instant CSS fallback |

## Problems / Technical Debt

- The initial JavaScript bundle grew 19,160 gzip bytes (14.7%) from Stage 23
  because the command palette activates more of the already-installed React Aria
  overlay/list behavior; it remains 41.5% below the gate.
- The Vite build still warns that the single minified JavaScript chunk exceeds
  500 kB before compression; route-level code splitting remains a measured
  optimization candidate, not a Stage 24 requirement.
- Component interaction and automated accessibility evidence use jsdom. Real
  View Transition paint behavior, INP, keyboard/browser differences, computed
  contrast, forced colors, zoom/reflow, and screen readers belong to Stage 25.
- The palette has twelve bounded items and intentionally is not virtualized.
- Arbitrary docking, animated numbers, springs, canvas, and WebGL remain rejected
  until a measured route demonstrates a need.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` records Stage 24 complete, the native interaction decisions,
34-test result, bundle delta/gate, smoke evidence, remaining browser-validation
limitations, and the Stage 25 approval gate.

## Next Stage

Stage 25 — Responsive, Accessibility & Performance Pass. No Stage 25 implementation was started.
