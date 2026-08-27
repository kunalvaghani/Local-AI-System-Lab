# Frontend Design Rationale

## Product metaphor

The frontend is an engineering instrument: part operating-system inspector,
profiler, trace debugger, and controlled experiment laboratory. It deliberately
avoids a chat-first surface, generic admin template, decorative neon AI styling,
and unrelated card grids. The approved direction is documented in the [frontend
research](../frontend-research.md) and [design system](../frontend-design-system.md).

## Information architecture

Twelve shallow URL-addressable domains are grouped into Observe, Investigate,
Test, and System. Runtime is the entry point; Agent/Scheduler views explain
ownership and movement; Trace/Replay explain causality; Hardware/Metrics explain
resource behavior; Chaos/Security explain controlled failure and defense.

URL task identity, TanStack Query server state, native EventSource reducer state,
ephemeral viewer state, and device preference state have separate owners. Only a
versioned density preference uses browser storage. Runtime evidence remains
server-owned.

## Visual and interaction decisions

- Graphite/warm-neutral surfaces and restrained cool accents reserve stronger
  colors for health, warning, failure, and selection evidence.
- Compact typography and a four-pixel spacing rhythm support dense technical
  inspection without sacrificing hierarchy.
- Native History links preserve deep routes, modifier-click, and back/forward.
- React Aria owns command-palette behavior; native View Transitions are bounded
  progressive enhancement with immediate/reduced-motion fallback.
- The workspace/evidence split is accessible and resettable; container queries
  follow actual pane width rather than viewport assumptions.
- Charts are implemented with semantic meters, tables, lists, and bounded CSS
  bars where those forms communicate the accepted data. No chart/WebGL library
  was justified by the current evidence.

## Performance and accessibility boundaries

Lifecycle bursts commit once per animation frame, retaining 200 events and
rendering 30. Trace responses render 100 rows per page even for a 10,000-step
fixture. Query owners use explicit 1–60 second cadences and abort signals;
metrics avoids duplicate live hardware probing.

Five viewport sizes, keyboard focus paths, reduced motion, calculated dark-theme
contrast, real Chromium accessibility structure, slow responses, and automated
axe scans were verified. The Stage 26 build is 150,997 gzip JavaScript bytes
against a 256,000-byte gate.

This is not a WCAG conformance claim. Human NVDA/JAWS/VoiceOver, forced-color,
400% zoom, cross-browser, heap/long-task, and field-INP work remain open.

## Why dependencies stayed small

React, React Aria, TanStack Query, and react-resizable-panels solve commodity
rendering, accessible interaction, server-state ownership, and splitting. A
router, chart library, terminal, editor, graph engine, animation runtime,
virtualizer, canvas, or WebGL layer was rejected or deferred because the current
routes pass their usability and bundle constraints without them.
