# Frontend Research — Stage 17

Research date: 2026-08-25  
Scope: research and recommendation only; no production frontend implementation  
Target: single-user, loopback Local AI Systems Lab backend accepted in Stage 16

## Decision summary

Recommend a custom **Systems Cartography** interface: a dense, keyboard-capable
runtime workbench that combines an operating-system inspector, profiler, trace
debugger, and controlled experiment laboratory. It should use a restrained
graphite/neutral foundation, explicit state typography and symbols, and color
only as a secondary signal. The interface should feel engineered for this
runtime rather than inherited from Material, a generic admin template, or a
chat product.

The lean recommended technical direction is React 19.2, TypeScript, Vite 8,
native CSS design tokens/CSS Modules, React Aria Components, TanStack Query,
TanStack Table and Virtual, and react-resizable-panels. React Flow and Recharts
should be route-level lazy dependencies used only where a graph or chart makes
the relationship materially clearer. Prefer native CSS transitions and the
View Transition API as progressive enhancement; add Motion only if Stage 18
prototypes prove native motion insufficient.

This recommendation is not an implementation authorization. Stage 18 must turn
an approved direction into a design system and UI architecture before real UI
features begin.

## What Stage 17 is for

Stage 17 replaces aesthetic guessing with current evidence. It studies how
Google, browser vendors, developer tools, observability products, and maintained
open-source projects solve hierarchy, density, navigation, streaming state,
traces, graphs, motion, performance, and accessibility. It then maps those
lessons onto the backend that actually exists.

## Research method and evidence rules

- Fresh searches were run on 2026-08-25 through Firecrawl and primary-source
  web search.
- Official documentation, official product changelogs, and canonical GitHub
  repositories are preferred over listicles and screenshots without context.
- `Verified` means the linked source directly supports the statement.
- `Inference` means the recommendation is derived from the source and project
  constraints; it is not a claim made by the source.
- Living documentation without a reliable publication date is labelled with
  the access date rather than assigned a fabricated release date.
- Bundle/performance impact is qualitative unless the source publishes a
  measurement. Stage 18/19 must measure the selected implementation.
- Proprietary products are interaction references only. Their branding,
  implementation, pricing, and visual identity are not dependencies.

## Backend facts that constrain the frontend

| Backend fact | Frontend consequence |
| --- | --- |
| Single-user loopback API | A client-rendered local application is sufficient; SSR and a public deployment platform add no demonstrated value |
| JSON request/response plus SSE lifecycle stream | Use a typed REST cache plus one owned `EventSource` stream per inspected active task |
| Tasks expose lifecycle, result, error, state history, metrics, and links | Task detail should be an inspector, not a chat transcript |
| Traces expose redacted ordered steps and deterministic replay | Tree/timeline views need explicit determinism, integrity, and replay labels |
| Scheduler, hardware, models, metrics, chaos, and security have separate endpoints | The shell needs domain navigation and cross-links, not a single dashboard full of unrelated cards |
| Runtime maturity includes `PARTIAL` and `DEFERRED` | Missing output, unavailable models, and security limits must be first-class states rather than hidden warnings |
| API is not multi-user or internet-facing | Do not design account, organization, billing, collaboration, or remote-deployment architecture |

## Reference matrix

The 28 references below satisfy the requested Google, wider-web, GitHub,
recency, implementation, performance, accessibility, dependency, and readiness
coverage. Browser support means either a web-platform support statement or the
library/product's practical browser scope; it does not imply that this project
has tested that source.

### Google and web-platform references

| # | Source and date | Support / maintenance | Performance and accessibility impact | Cost, usefulness, readiness |
| ---: | --- | --- | --- | --- |
| 1 | [Material 3 Expressive for Android and Wear OS](https://blog.google/products-and-platforms/platforms/android/material-3-expressive-android-wearos-launch/), Google, 2025-05-13 | Current Google product direction; native Android/Wear OS rather than a web component library | Verified: responsive components, emphasized type, glanceable information, and spring-like feedback. Inference: borrow emphasis and feedback principles, not mobile shapes or excessive bounce | No web dependency. Useful for hierarchy and purposeful feedback. Production product direction, not a web stack |
| 2 | [Material canonical layouts](https://m3.material.io/foundations/layout/canonical-examples/overview), living Material 3 guidance, accessed 2026-08-25 | Current design guidance; compact/medium/expanded examples | Verified: list-detail and supporting-pane patterns adapt across breakpoints. Accessibility depends on the implementation | No dependency. Highly useful for inspector panes. Production-ready design guidance |
| 3 | [Material interaction states](https://m3.material.io/foundations/interaction/states/overview), living guidance, accessed 2026-08-25 | Current Material guidance | Verified: states should use two visual indicators and consistently represent hover, focus, press, selection, and drag | No dependency. Directly useful for runtime states. Production-ready guidance |
| 4 | [People + AI Guidebook](https://pair.withgoogle.com/guidebook-v2/), Google PAIR, 2019; updated 2021 | Older but still public human-centered AI guidance | Verified: mental models, explainability, user control, and graceful failure. It does not cover current React/browser implementation | No dependency. Foundational for explaining routing, uncertainty, and failure; mature guidance |
| 5 | [What's New in Web UI — I/O 2025](https://developer.chrome.com/blog/new-in-web-ui-io-2025-recap), Chrome Developers, 2025 | Current browser UI survey; individual features have different support | Verified: native dialog/popover and anchor positioning reduce custom positioning/focus code. Progressive enhancement remains necessary | Zero library cost. Useful for menus/tooltips. Mixed: popover production-ready; some linked features still maturing |
| 6 | [What's New in Web UI — 2026](https://developer.chrome.com/blog/new-in-web-ui-io26), Chrome Developers, 2026 | Chrome 147 includes element-scoped view transitions; cross-browser support varies by subfeature | Verified: subtree transitions can keep the rest of the page interactive. Inference: limit use to local inspector changes and never require it | Zero library cost. Useful progressive enhancement; scoped/two-phase features remain experimental or uneven |
| 7 | [What's new in View Transitions — 2025](https://developer.chrome.com/blog/view-transitions-in-2025), Chrome Developers, 2025-10-08 | Same-document transitions reached broad modern-browser availability; types/scoped extensions varied | Snapshotting can simplify state-change animation but can increase paint/memory cost on large surfaces. Must honor reduced motion | Zero dependency. Useful for list-detail continuity. Core production-capable; extensions progressive/experimental |
| 8 | [Baseline 2025](https://web.dev/baseline/2025), web.dev, 2025 | Tracks features available across the core browser set | Verified: popover, view transitions, `@scope`, and related features entered Baseline during 2025 | Zero dependency. Use as the support gate instead of browser folklore. Production guidance |
| 9 | [`content-visibility`](https://web.dev/articles/content-visibility), web.dev; Baseline Newly Available 2025-09-15 | All three major engines per the source | Verified: skips off-screen rendering and can improve INP, while off-screen content generally remains in the accessibility tree. Requires careful hidden-landmark handling | Zero dependency. Useful for coarse inspector sections, not a replacement for list virtualization. Production-capable with accessibility audit |
| 10 | [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/), W3C WAI, living standard guidance | Browser/assistive-technology behavior still requires testing | Verified keyboard/focus patterns for grids, toolbars, dialogs, trees, and other composites | Zero dependency. Mandatory behavioral reference. Production guidance, not proof of conformance |

### Developer, observability, and AI-tool interaction references

| # | Source and date | Support / maintenance | Performance and accessibility impact | Cost, usefulness, readiness |
| ---: | --- | --- | --- | --- |
| 11 | [Chrome DevTools documentation](https://developer.chrome.com/docs/devtools/), living, accessed 2026-08-25 | Continuously maintained with Chrome | Verified patterns include a command menu, data-dense panels, timelines, flame charts, streaming logs, filtering, and inspection. Do not infer full accessibility from its existence | No application dependency. Primary interaction reference for a debugging laboratory; production tool |
| 12 | [Grafana flame graph](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/flame-graph/), living docs, accessed 2026-08-25 | Actively maintained Grafana documentation | Verified drill-down, focus, sandwich view, grouping, diff values, and a status bar. Dense canvas/SVG views require keyboard and text alternatives | Reference only. Excellent model for hierarchical cost inspection; production product |
| 13 | [SigNoz Trace Explorer](https://signoz.io/docs/userguide/traces/), updated 2026-07-27 | Actively maintained open-source product | Verified list, trace, time-series, and table modes; quick filters; column control; export; saved views. Multiple modes help accessibility but do not guarantee it | Reference only. Strong model for progressive disclosure and equivalent views; production product |
| 14 | [Langfuse New Trace View](https://langfuse.com/changelog/2025-03-19-new-trace-view), 2025-03-19 | Shipped product feature; project remains active | Verified hierarchy, tree/timeline toggle, search, view settings, metrics, and scores. Toggling views avoids forcing one visualization onto every task | Reference only. Directly useful for Local AI traces; production feature |
| 15 | [Langfuse trace best practices](https://langfuse.com/docs/observability/best-practices), living docs, accessed 2026-08-25 | Active official documentation | Verified trace tree and agent-graph representations. Inference: stable task/step naming should drive search and cross-view selection | Reference only. Useful domain model; production guidance |
| 16 | [PostHog tracing viewer state split](https://github.com/posthog/posthog/issues/69890), merged work described 2026-07 | Active open-source product; evidence includes passing frontend suites and bundle reports | Verified architectural lesson: URL state, viewer state, and query state should be separate; embedded viewers must refresh without router side effects | Reference only. Highly useful for Stage 18 UI state boundaries. Production-oriented implementation evidence |

### Open-source implementation candidates

| # | Source and date | Support / maintenance | Performance and accessibility impact | Cost, usefulness, readiness |
| ---: | --- | --- | --- | --- |
| 17 | [React 19.2](https://react.dev/blog/2025/10/01/react-19-2), 2025-10-01 | Stable release; official blog current in 2026 | Verified `Activity` and DevTools performance tracks. React's `ViewTransition` remained canary in the cited research, so do not base production motion on it | Core dependency. Strong fit for a stateful inspector; production-ready stable channel only |
| 18 | [Vite 8](https://vite.dev/blog/announcing-vite8), 2026-03-12 | Stable; Vite 8.1 followed in 2026 | Verified unified Rolldown bundler and official React plugin. Client build avoids an unnecessary application server | Core build dependency. High usefulness and low architectural overhead; production-ready |
| 19 | [React Aria Components](https://react-spectrum.adobe.com/react-aria/getting-started.html) and [repository](https://github.com/adobe/react-spectrum), release evidence 2026-04-15; active PRs in 2026-08 | Actively maintained by Adobe; modern React/browser target | Verified unstyled components cover accessibility, internationalization, focus, keyboard, touch, and assistive-technology concerns. Styling remains project-owned | Core primitive dependency. Replaces overlapping primitive libraries. Production-ready, still requires project testing |
| 20 | [react-resizable-panels](https://github.com/bvaughn/react-resizable-panels), releases through 4.12.1 on 2026-07-03 | Active, small focused repository | Verified WAI-ARIA-aligned `Separator`, keyboard handling, persisted layouts, and fixes for pointer/focus edge cases. Resize events can create layout work, so throttle expensive children | One focused dependency. Best fit for desktop inspector panes; production-ready |
| 21 | [TanStack Virtual performance and iOS update](https://tanstack.com/blog/tanstack-virtual-perf-and-ios), 2026-05-19 | Active; current docs include streaming/end-anchored list work | Published measurements: 100k cold mount 6.1→4.5 ms and a 10k resize storm nearly 2 s→1.3 ms. Virtualization complicates focus, search, height measurement, and screen-reader position semantics | Focused dependency. Essential for large traces/events; production-ready with explicit accessibility policy |
| 22 | [TanStack Query](https://tanstack.com/query/latest/docs/framework/react/installation), living docs accessed 2026-08-25 | Actively maintained; React 18+ and current evergreen browser targets documented | Verified cache, structural sharing, tracked properties, and selector-based subscriptions reduce redundant work. It does not own SSE ordering or task lifecycle semantics | Core server-state dependency. Pair with a small owned EventSource adapter; production-ready |
| 23 | [TanStack Table](https://tanstack.com/table/latest), living current docs | Actively maintained; current docs advertise headless table/data-grid infrastructure | Headless sorting/filtering/grouping/column state avoids a large visual framework. Interactive grid keyboard behavior remains our responsibility through React Aria/APG | Focused dependency. Useful for tasks, traces, models, and evidence tables; production-ready |
| 24 | [React Flow / xyflow](https://github.com/xyflow/xyflow), active releases in 2026 | Maintained team project; MIT | Node UIs provide pan/zoom and customization but can be expensive and difficult for keyboard/screen-reader users at scale. Always provide an equivalent tree/list | Lazy optional dependency. Useful for agent/state topology, not the default trace view; production-ready with accessibility fallback |
| 25 | [Recharts releases](https://github.com/recharts/recharts/releases), stable 3.8.0 on 2026-03-06; 3.9 canary in 2026-06 | Active maintainers and current releases | SVG/React composition is approachable and supports bounded metric series; large point counts and animated charts can stress DOM/reconciliation. Provide data tables and disable nonessential animation | Lazy chart dependency. Good initial fit for local bounded telemetry; stable release only |
| 26 | [cmdk](https://github.com/dip/cmdk), living repository accessed 2026-08-25 | Repository moved from `pacocoursey` to `dip`; current page shows open work but no clear recent stable release | Official README claims VoiceOver/Chrome testing and 2k–3k item performance but says no virtualization and notes risky manual DOM ordering/concurrency uncertainty | Reject from core stack. React Aria can supply command-palette primitives with fewer overlapping dependencies; reconsider only after prototype evidence |
| 27 | [xterm.js](https://github.com/xtermjs/xterm.js), active commits through 2026-08-18 | Very active; stable/beta channels documented | Mature terminal rendering and contrast/accessibility work, but WebGL/IME/disposal issues remain active and it is costly if the backend has no terminal protocol | Defer. No current backend terminal endpoint exists; production-capable when a real terminal use case is approved |
| 28 | [Motion accessibility guidance](https://motion.dev/docs/react-accessibility), living docs accessed 2026-08-25 | Active Motion project | Verified global reduced-motion support and replacement of large transforms with opacity. Any animation library adds JS and can compete with streaming/chart work | Optional lazy dependency only if native CSS is insufficient. Production-ready, but not justified by novelty |

## Recency review: approximately the previous 6–12 months

| Change | Why it matters here | Decision |
| --- | --- | --- |
| React 19.2 stable, 2025-10 | `Activity` can preserve expensive inspector state; performance tracks improve profiling | Use stable `Activity` only after measuring memory; do not use canary ViewTransition APIs |
| Same-document view transitions reached broad availability during 2025; transition types became Baseline 2026 | Inspector selection can retain spatial context without a motion framework | Progressive enhancement only; instant state change remains the fallback |
| `content-visibility` reached Baseline in 2025-09 | Large below-fold inspector sections can avoid unnecessary rendering | Use for coarse sections after accessibility tests; use real virtualization for long rows |
| Vite 8 stable, 2026-03 | A local client app gets a fast, simple build without SSR infrastructure | Recommended build tool |
| React Aria Components active release, 2026-04 | Accessible unstyled primitives remain actively maintained | Recommended primitive layer |
| TanStack Virtual major performance/iOS work, 2026-05 | Deep trace trees, events, and streaming histories need current virtualization behavior | Recommended, with focus/search semantics tested |
| Recharts 3.8 stable, 2026-03; 3.9 canary, 2026-06 | Chart maintenance is active, while new animation APIs are not yet stable | Pin stable; turn default chart animation off for live telemetry |
| react-resizable-panels 4.12.1, 2026-07 | Current ARIA-aligned split-pane fixes reduce custom pointer/keyboard code | Recommended desktop layout primitive |
| PostHog trace viewer separation, 2026-07 | Current production evidence supports separating URL, query, and viewer state | Adopt the boundary in Stage 18 architecture |
| SigNoz Trace Explorer docs, 2026-07 | Current observability UI uses equivalent list/trace/time-series/table modes | Adopt equivalent views instead of graph-only inspection |
| xterm.js active through 2026-08 | A terminal component remains viable, but only with a real protocol/use case | Defer; do not add a decorative terminal |

## Recommended information architecture direction

Stage 18 should refine this, but research supports the following hierarchy:

```text
Global shell
├── Runtime Command Center
├── Tasks
│   └── Task inspector: summary | lifecycle | trace | metrics | raw evidence
├── Agents
├── Scheduler
├── Models
├── Hardware
├── Traces & Replay
├── Chaos Lab
├── Security Evidence
├── Metrics
└── Settings / About this build
```

The initial route should answer three questions without opening another page:

1. Is the runtime healthy and safe to accept work?
2. What is executing or queued, and why?
3. Where did time and resources go in the selected task?

## Interaction ideas mapped to real API surfaces

| Interaction | Component behavior | Real API source |
| --- | --- | --- |
| Runtime pulse strip | Compact status, queue depth, selected model, RAM/VRAM pressure, and active task; no decorative gauges | `/v1/health`, `/v1/scheduler`, `/v1/hardware`, `/v1/models` |
| Task list-detail workspace | Virtualized task/event list on the left, selected task inspector on the right; mobile becomes stacked navigation | Task creation response, `/v1/tasks/{id}`, SSE links |
| Live execution rail | Append lifecycle events in order, preserve the terminal event, pause visual following when the user scrolls away | `/v1/tasks/{id}/events` |
| State-machine path | Text-first ordered states with duration bars; illegal/unvisited states remain visually distinct | Task `state_history` |
| Trace dual view | Default accessible tree/list; optional timeline with synchronized selection and details | `/v1/tasks/{id}/trace`, `/v1/traces/{run_id}` |
| Replay evidence drawer | Integrity result, reconstructed state, matches/divergences, skipped nondeterministic/side-effecting steps | `/v1/traces/{run_id}/replay` |
| Resource admission explanation | Show measured input, estimate, decision, reason, and recommendation in that order | Task metadata, `/v1/hardware` |
| Command palette | Navigate domains, open a known task/run, focus filters, and invoke only currently permitted commands | Client navigation plus documented safe API actions |
| Chaos confirmation flow | Scenario scope, isolated-runtime warning, typed confirmation, and retained result; never a one-click destructive icon | `/v1/chaos` |
| Security evidence view | Case table with PASS/FAIL, evidence, date, scope, and an always-visible “not certification” boundary | `/v1/security/results` |

## Animation and transition ideas

Motion communicates causality; it does not decorate idle screens.

- Use 120–180 ms opacity/color transitions for state and selection changes.
- Use a short shared-element or view transition only when moving from a task row
  into its inspector; the task identity must remain visible throughout.
- Animate a newly appended trace/event row once, then leave it stable.
- Move a scheduler item only when its actual order changes; announce the change
  textually and never continuously float queued work.
- Use duration-bar growth only while time is genuinely accumulating.
- Avoid animated gradients, background particles, parallax, cursor trails,
  looping “AI thinking” effects, and constantly pulsing healthy states.
- Under `prefers-reduced-motion`, remove transforms, graph interpolation, and
  automatic scrolling; retain brief opacity or instant changes.
- Pause live-follow when selection, keyboard focus, or manual scroll indicates
  that the user is inspecting history.

## Visual direction proposals

### A. Systems Cartography — recommended

- Graphite and warm-neutral surfaces with one quiet cool accent.
- Dense typographic hierarchy: operational labels, tabular numerals, and clear
  state verbs instead of oversized marketing headings.
- A narrow global rail, a flexible central work surface, and a contextual
  evidence pane.
- Thin relationship lines, duration bars, state glyphs, and resource contours
  evoke system maps and profilers without pretending the runtime is distributed.
- Status uses symbol + label + tone. Red is reserved for active failures or
  destructive confirmation, never general decoration.

Why: it communicates runtime topology, inspection, and engineering evidence
while remaining distinct from generic dashboards and chat interfaces.

### B. Instrument Bench

- Dark, high-density profiler aesthetic with monospace-heavy labels, compact
  tables, and persistent lower evidence drawer.
- Excellent for focused debugging, but risks reduced readability, “terminal as
  decoration,” and poor daylight/light-theme use.

Decision: retain as an optional density/theme influence, not the sole direction.

### C. Adaptive Material Laboratory

- Material-style list-detail/supporting panes, expressive type, shape changes,
  and spring feedback.
- Strong adaptive-layout research base, but direct adoption would make the
  project feel like an Android or generic Material application.

Decision: borrow adaptive hierarchy and double-coded states; reject the visual
skin and high-motion personality.

## Recommended frontend stack

| Layer | Recommendation | Why | Constraint |
| --- | --- | --- | --- |
| Application | React 19.2 + TypeScript | Stable stateful UI base with mature ecosystem | Stable APIs only; no canary React features |
| Build | Vite 8 | Client-only local app; fast, low-infrastructure build | Pin exact versions in Stage 18 after compatibility verification |
| Routing | URL-addressable client routing with route-level lazy modules | Trace/task links must survive refresh and be shareable locally | Select the smallest maintained router during Stage 18 architecture, not by habit |
| Server state | TanStack Query | Typed REST caching, invalidation, structural sharing | SSE ordering and lifecycle ownership stay in a project adapter |
| Live state | Small owned `EventSource` adapter + reducer | Backend already uses SSE; order, reconnect, terminal close, and cursor semantics are domain logic | One stream per inspected active task; close on terminal/unmount |
| Primitives | React Aria Components | Accessible unstyled behavior without importing a visual identity | Test actual keyboard, screen reader, touch, and high-contrast behavior |
| Styling | CSS custom properties + CSS Modules + modern native CSS | Keeps the design system inspectable and prevents framework-default appearance | Establish tokens and browser baseline in Stage 18 |
| Panels | react-resizable-panels | Current accessible split-pane behavior and persistence | Desktop enhancement; mobile uses stacked routes/sheets, not tiny split panes |
| Dense data | TanStack Table + TanStack Virtual | Headless tables plus current large-list performance | Preserve row identity, focus, search, and screen-reader counts |
| Graph | React Flow, lazy | Appropriate for agent/state topology and interactive selection | Always provide tree/list equivalent; cap visible nodes and avoid force motion |
| Charts | Recharts stable, lazy | Maintainable for bounded local telemetry | Downsample/bound points, disable live animation, provide numeric/table alternative |
| Motion | Native CSS/View Transitions first; Motion deferred | Most proposed transitions do not need a runtime dependency | Add Motion only after measured Stage 18 prototype need |
| Testing | Vitest, Testing Library, Playwright, axe-core, manual screen-reader/keyboard checks | Unit, component, real-browser, automated accessibility, and human assistive-tech coverage | Automated accessibility checks are not certification |

### Dependency policy

Start with the core application, query, accessible primitives, panel, table, and
virtualization packages. Graph, chart, syntax, editor, terminal, and animation
packages must be separately lazy-loaded and justified by a real route. Record
bundle deltas before keeping each optional dependency.

## Proposed performance constraints for Stage 18 validation

These are budgets to test, not measurements or completed guarantees.

- Keep the initial shell route at or below 250 KiB compressed JavaScript,
  excluding lazy graph/chart/debugger routes.
- Do not render more than the visible event/trace window plus bounded overscan.
- Coalesce visual hardware/metric refreshes to a human-readable cadence; do not
  rerender the application for every raw metric sample.
- Batch SSE-derived React updates at most once per animation frame while
  preserving event order and immediate terminal/error delivery.
- Cap chart point counts per visible series and retain raw values for inspection.
- Lazy-load graph, chart, JSON/code, and future terminal components.
- Measure INP, long tasks, heap growth, first route load, task-stream update cost,
  and trace-open time using deterministic fixture sizes.
- Define small/medium/large fixtures, including at least a 10,000-step trace,
  before claiming virtualization or interaction performance.

## Accessibility requirements carried into Stage 18

- Target WCAG 2.2 AA and test, rather than infer, conformance.
- Every status uses text plus icon/shape; color is never the only signal.
- Keyboard users can reach every route and action without traversing thousands
  of cells; composite widgets follow APG focus patterns.
- Resizable separators have visible focus, keyboard resizing, current value,
  and a reset mechanism.
- Graphs, timelines, and charts provide equivalent ordered lists/tables and
  synchronized selected-item details.
- Streaming updates do not steal focus or flood a live region. Announce only
  important state changes and terminal outcomes.
- Motion respects `prefers-reduced-motion`; automatic follow/scroll can be
  paused and never resumes unexpectedly.
- Dense mode still maintains usable targets, zoom up to 400%, reflow, contrast,
  and visible focus.
- Error, `PARTIAL`, `DEFERRED`, unavailable, missing-output, and stale states
  have distinct language and recovery guidance.
- Test Windows high contrast, keyboard-only operation, screen magnification,
  reduced motion, and at least NVDA with Chrome/Firefox on the target machine.

## Rejected or deferred ideas

| Idea | Decision | Reason |
| --- | --- | --- |
| Direct Material 3 visual clone | Reject | Loses project identity and imports mobile/product assumptions; retain hierarchy/adaptive lessons only |
| Generic dashboard card grid | Reject | Hides relationships among task, scheduler, trace, model, and hardware evidence |
| ChatGPT-style transcript as the main UI | Reject | The system is a runtime inspector; tasks, states, traces, and resource decisions are primary |
| Full arbitrary docking/window manager | Defer | High state, focus, persistence, mobile, and accessibility cost; two resizable panes cover the demonstrated need |
| Canvas/WebGL everywhere | Reject | Text selection, accessibility, testing, and low-end GPU coexistence suffer; reserve for a proven large-graph bottleneck |
| Monaco editor | Defer | No current code-editing contract; large dependency and worker cost |
| xterm.js terminal | Defer | No terminal backend endpoint; a fake terminal would be decoration |
| cmdk plus React Aria/Radix primitives | Reject initially | Overlapping primitive behavior and cmdk's own virtualization/concurrency caveats increase dependency and audit cost |
| Motion on every component | Reject | Competes with live visualization and creates accessibility/performance risk without informational value |
| Experimental React ViewTransition APIs | Reject for production | Canary API may change; native view transitions can be progressive enhancement |
| Next.js/RSC/SSR | Reject for current scope | Loopback client app has no SEO/public-server requirement; adds a server and security surface |
| Tailwind/shadcn as the visual foundation | Defer | Fast scaffolding can pull the result toward a recognizable generic aesthetic; custom tokens/CSS better demonstrate the approved design system |
| Heavy blur/glass/neon “AI” styling | Reject | Reduces density, contrast, and technical credibility while consuming paint budget |

## Visual evidence and demo links

No third-party screenshots are copied into the repository. These official pages
contain screenshots or live examples that can be reviewed legally in context:

- [Material canonical layout examples](https://m3.material.io/foundations/layout/canonical-examples/overview)
- [Material 3 Expressive product examples](https://blog.google/products-and-platforms/platforms/android/material-3-expressive-android-wearos-launch/)
- [Chrome Web UI 2025 demos](https://developer.chrome.com/blog/new-in-web-ui-io-2025-recap)
- [Chrome Web UI 2026 demos](https://developer.chrome.com/blog/new-in-web-ui-io26)
- [SigNoz Trace Explorer screenshots](https://signoz.io/docs/userguide/traces/)
- [Langfuse trace tree/timeline examples](https://langfuse.com/changelog/2025-03-19-new-trace-view)
- [Grafana flame graph interaction examples](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/visualizations/flame-graph/)
- [React Flow examples](https://reactflow.dev/examples)
- [react-resizable-panels examples](https://react-resizable-panels.vercel.app/)

## Stage 18 questions requiring explicit design decisions

1. Approve Systems Cartography as the primary visual direction, or select one of
   the alternatives/influences.
2. Define the exact application navigation and URL model from current API
   resources.
3. Establish typography, density, themes, color/state tokens, spacing,
   breakpoints, and motion tokens.
4. Prototype and test the task list-detail workspace at compact, medium, and
   expanded widths.
5. Measure the proposed core stack and optional visualization chunks before
   accepting dependencies.
6. Define fixture sizes and accessibility acceptance tests before building live
   runtime screens.

## Stage 17 stopping point

Research and recommendation are complete. No frontend directory, package,
component, stylesheet, route, generated design asset, production UI, or new
runtime behavior was created. Stage 18 may begin only after explicit approval.
