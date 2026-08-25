# Frontend Design System and UI Architecture — Stage 18

## Decision summary

The frontend adopts the Stage 17 **Systems Cartography** direction: a local,
evidence-first engineering instrument with graphite and warm-neutral surfaces,
a quiet cool accent, compact operational typography, and three persistent
spatial roles:

1. a global domain rail,
2. a flexible primary workspace,
3. a contextual evidence pane.

The Stage 18 prototype lives in `apps/web`. It is a local React/TypeScript/Vite
application. It deliberately makes no API request and shows no simulated
runtime telemetry. Stage 19 will connect the runtime route to the real loopback
API without replacing the shell architecture.

## Design principles

1. **Evidence before inference.** A value needs a named source, state, and unit.
2. **State before decoration.** Tone and motion communicate operational change.
3. **Relationships before cards.** Layout preserves task-to-runtime-to-evidence
   context rather than fragmenting it into an unrelated dashboard grid.
4. **Dense, never cramped.** Comfortable and compact density share semantics,
   hierarchy, and usable controls.
5. **Equivalent truths.** Graphs, timelines, and charts are projections of an
   ordered text/table representation, never a separate source of truth.
6. **Local by construction.** Browser requests will use relative `/v1` paths
   proxied to the literal loopback API; no hosted service is introduced.

## Foundations

### Typography

| Role | Token/implementation | Purpose |
| --- | --- | --- |
| Interface | `--font-ui` | System UI stack for navigation and long-form reading; no network font dependency |
| Evidence | `--font-data` | Cascadia Code/Consolas-style stack for IDs, endpoints, units, times, and hashes |
| Route title | 28–44 px fluid, weight 540 | Strong orientation without marketing-scale headings |
| Section title | 22–32 px fluid, weight 530 | Groups a bounded work surface |
| Body | Browser default 16 px | Explanations and recovery guidance |
| Operational label | 10–12 px, tracked uppercase | Eyebrows, sources, units, compact metadata |
| Numeric data | Evidence font with tabular numerals | Comparable telemetry columns and changing values |

Large blocks of prose never use the evidence font. IDs and numbers never depend
on proportional alignment.

### Spacing

The base rhythm is 4 px. Tokens are `4, 8, 12, 16, 24, 32, 48` px
(`--space-1` through `--space-7`). Components consume tokens rather than raw
spacing values. Compact density reduces intermediate layout gaps and control
height while preserving legibility and target access.

### Color system

| Semantic role | Token | Stage 18 value |
| --- | --- | --- |
| Canvas | `--color-canvas` | `#0c0e0c` |
| Surface 1 | `--color-surface-1` | `#111310` |
| Surface 2 | `--color-surface-2` | `#171a16` |
| Surface 3 | `--color-surface-3` | `#1d211c` |
| Raised | `--color-surface-raised` | `#232820` |
| Primary text | `--color-text` | `#f1f2ea` |
| Muted text | `--color-text-muted` | `#9da596` |
| Quiet accent | `--color-accent` | `#8db4ff` |
| Positive | `--color-positive` | `#77c99a` |
| Warning | `--color-warning` | `#e2b86b` |
| Critical | `--color-critical` | `#f08378` |
| Focus | `--color-focus` | `#b9d0ff` |

Red is reserved for active failures and destructive confirmation. Healthy state
does not pulse. Status always combines glyph, label, and tone. The current
prototype is dark-first; a light theme is deferred until the operational views
establish real contrast requirements.

### Surfaces, depth, borders, and shape

- Canvas is the coordinate plane.
- Surface 1 owns persistent shell chrome.
- Surface 2 owns grouped work.
- Surface 3 marks selection or nested evidence.
- Raised surface is limited to temporary overlays or floating context.
- One-pixel low-contrast borders express hierarchy and relationships.
- Strong borders identify selection, focus adjacency, or resizing.
- Shadows are not used to make ordinary content resemble floating cards.
- Radii are 4, 8, and 12 px; pill geometry is reserved for status/metadata.

### Iconography

- Navigation always retains a visible text label; an icon never becomes the
  only way to identify a domain.
- Stage 18 uses two-letter domain glyphs to avoid an unnecessary icon package.
- Operational state uses a small fixed glyph vocabulary paired with text.
- Future pictograms should be 1.5–2 px monoline forms on a 16 or 20 px grid,
  use `currentColor`, and be hidden from assistive technology when redundant.
- Brand, state, and destructive icons may not be reused interchangeably.

## Operational states

The reusable `StatusToken` contract covers:

| State | Meaning | Required companion behavior |
| --- | --- | --- |
| Healthy | Current evidence is within an accepted boundary | Include source time where freshness matters |
| Active | Work is executing now | Motion optional; label remains stable |
| Queued | Accepted but not executing | Show order/reason when available |
| Warning | Pressure or recoverable concern | Explain threshold and mitigation |
| Critical | Active failure | Explain impact and recovery action |
| Blocked | Policy/resource prevents execution | Show decision authority and reason |
| Partial | Capability/evidence is incomplete | Preserve scope and missing portion |
| Deferred | Intentionally outside current scope | Name the owning later stage |
| Unavailable | Source did not provide a value | Never substitute zero |
| Stale | Last valid evidence exceeds freshness policy | Retain timestamp and stop implying live state |
| Unknown | No supported interpretation exists | Preserve raw safe evidence if available |

The known terminal-output atomicity gap must render as completed state plus
missing-output evidence; it must never be silently converted to success.

## Motion principles

- Fast feedback: 120 ms.
- Standard selection/state change: 180 ms.
- Approved easing: `cubic-bezier(0.2, 0, 0, 1)`.
- A row may animate once when real evidence appends; it then becomes stable.
- Scheduler movement occurs only when actual ordering changes.
- Duration bars grow only while their underlying duration is accumulating.
- Route changes prioritize immediate orientation; no decorative page sweep.
- `prefers-reduced-motion` reduces all transitions to effectively immediate.
- No looping particles, animated gradients, cursor trails, idle pulse, or
  synthetic “thinking” animation.

## Data visualization principles

Every visualization must define:

1. metric and unit,
2. source and confidence,
3. time window and freshness,
4. missing/stale behavior,
5. selection relationship to the evidence pane,
6. numeric table/list alternative,
7. point/node bound and reduction method.

Color differentiates series only after label/shape. Live charts disable default
animation. Zero is data; unavailable is absence. Estimates, measured samples,
budgets, and limits remain visually and textually distinct. Graph and timeline
modules stay lazy and cannot block the initial shell.

## Density modes

| Mode | Use | Contract |
| --- | --- | --- |
| Comfortable | Default exploration and touch-adjacent use | 36 px controls, full spacing rhythm |
| Compact | Keyboard/mouse inspection and large tables | 30 px controls, reduced gaps; no semantic or content removal |

The versioned density preference is the only Stage 18 browser-persisted value:
`local-ai-lab:preferences:v1:density`. Runtime data, task state, filters, and
security evidence are never copied to browser storage by the prototype.

## Layout grid and breakpoints

### Expanded: above 1100 px

- 216 px global domain rail.
- Resizable workspace/evidence split, initially 76/24.
- Evidence pane minimum 256 px and maximum 45%.
- Horizontal separator exposes keyboard resizing and current value.

### Medium: 721–1100 px

- Persistent domain rail.
- Workspace/evidence becomes a vertical 68/32 split.
- The evidence relationship remains visible without squeezing it into a narrow
  side column.

### Compact: 320–720 px

- System bar stays visible.
- Domain groups become a horizontally scrollable labeled navigation strip.
- Workspace and evidence use a vertical inspector.
- Foundation/visualization grids become one column.
- Density control is hidden because compact layout already owns constrained
  space; stored density still applies to reusable controls.

Zoom and reflow remain required through 400%. Breakpoints represent layout
capability, not named devices.

## Reusable component contracts

| Component | What it does | Upgrade enabled |
| --- | --- | --- |
| `AppShell` | Composes global rail and responsive resizable inspector | Stable spatial model for every later runtime view |
| `SystemBar` | Identifies the build, connection boundary, and density | Persistent global context without fake health data |
| `DomainRail` | Groups and links all application areas | URL-addressable, keyboard-native information architecture |
| `RouteWorkspace` | Owns route heading, endpoint contract, and primary content | Future live routes replace content, not the shell |
| `EvidencePane` | Displays selected/source context | Keeps claims adjacent to provenance and details |
| `StatusToken` | Double-codes eleven operational states | Prevents success-only and color-only interfaces |
| `DesignSystemView` | Interactively demonstrates foundations/states/visualization | Makes the language inspectable rather than documentation-only |
| Pane separator | Pointer/keyboard resizing and reset behavior | Dense desktop inspection with an accessible adjustment control |
| Density control | Switches comfortable/compact tokens | User-controlled information density with versioned local preference |

## Application information architecture

```text
Observe
├── /runtime                 Runtime Command Center
├── /tasks                   Task collection
│   └── /tasks/:taskId       Task inspector
├── /agents                  Agent registry/state
└── /scheduler               Queue and admission

Investigate
├── /models                  Registry, routing, profiles, budgets
├── /hardware                Capacity, pressure, admission inputs
├── /traces                  Trace collection
│   └── /traces/:runId       Trace and replay inspector
└── /metrics                 Unified telemetry

Test
├── /chaos                   Controlled fault laboratory
└── /security                Adversarial evidence, never certification

System
├── /design-system           Stage 18 interactive foundation
└── /settings                Device-local preferences and build scope
```

Stage 18 implements the twelve collection/top-level routes. Parameterized task
and trace detail routes are contracts for their owning later stages.

## Frontend state architecture

```text
Browser URL
  └── selected application domain and future shareable resource ID

Server query cache (Stage 19+)
  └── bounded REST snapshots keyed by endpoint parameters

Owned live stream reducer (Stage 19+)
  └── ordered task SSE events, cursor, reconnect, terminal close

Viewer state
  └── selected row/step, expanded nodes, follow mode, local panel state

Versioned device preference
  └── density only in Stage 18
```

These states do not mirror each other. A stream refresh cannot navigate. Viewer
selection cannot invalidate runtime state. A URL change explicitly owns resource
selection. Future API types must be derived from the OpenAPI/runtime payloads,
not from prototype-shaped fixture objects.

## Accessibility acceptance contract

- Target WCAG 2.2 AA; automated checks are evidence, not certification.
- Skip link reaches the primary workspace.
- Every application area is a native link with `aria-current`.
- Tabs and density selection use React Aria behavior.
- Pane separator exposes role, orientation, current value, and keyboard control.
- Status is never color-only.
- Focus remains visible against every surface.
- Streaming updates may announce only important state changes and terminal
  outcomes; they never move focus or flood a live region.
- Graphs/charts require synchronized list/table alternatives.
- Reduced motion, forced colors, 400% zoom, keyboard-only operation, and NVDA
  with Chrome/Firefox remain manual browser acceptance work for Stage 25.

## Performance contract

- Initial compressed JavaScript budget: 250 KiB.
- Stage 18 actual: 102,802 bytes gzip across one JavaScript asset.
- Specialized graph/chart/trace modules must be route-lazy.
- Future 10,000-step fixtures require virtualization and bounded overscan.
- Raw SSE order is preserved while React visual commits may be frame-coalesced.
- Terminal/error evidence bypasses low-priority visual batching.
- Browser INP, long tasks, heap growth, and trace-open cost require real-browser
  fixtures before performance claims.

## Stage boundary

Stage 18 owns the design system, responsive shell, top-level navigation,
resizable evidence layout, density preference, component examples, component
tests, accessibility scan, and bundle measurement. It does not own live API
queries, task creation, SSE, real telemetry, graphs, charts, traces, or command
actions. Those remain Stage 19 and later.
