# ADR-0018: Systems Cartography local web shell

- Status: Accepted
- Date: 2026-08-25
- Stage: 18

## Context

The Stage 16 backend is accepted for single-user loopback frontend work. Stage
17 compared current design guidance, developer/observability products, browser
capabilities, and maintained React libraries. It recommended a distinctive
Systems Cartography direction and rejected generic dashboards, chat clones,
arbitrary docking, and visualization dependencies without a real route.

Stage 18 needs a navigable prototype without coupling future live data to fake
frontend objects or introducing a public web service.

## Decision

Create `apps/web` as a local React 19.2/TypeScript/Vite 8 application with:

- custom CSS tokens and no visual framework,
- React Aria Components for accessible stateful primitives,
- react-resizable-panels for the bounded workspace/evidence split,
- native History API routing for the twelve shallow top-level routes,
- an explicit separation among URL, future server cache, future SSE reducer,
  viewer state, and device preferences,
- a graphite/warm-neutral evidence-first language,
- a 250 KiB compressed initial-JavaScript budget,
- explicit unavailable states and no simulated runtime telemetry.

Use the Vite development proxy for relative `/v1` requests to the literal
loopback backend in Stage 19. Do not deploy or expose either service remotely.

## Alternatives

### React Router or another routing dependency

Deferred. The Stage 18 route model is one shallow level and needs only history,
back/forward, deep-link, modifier-click, and native link semantics. The owned
adapter is small. Add a maintained router only when parameterized/nested route
behavior demonstrates enough complexity to justify it.

### Generic component framework or Tailwind/shadcn foundation

Rejected for the current design-system layer. It would import recognizable
visual defaults and make the approved language less inspectable.

### Arbitrary docking/window manager

Deferred. One accessible resizable relationship handles the demonstrated
workspace/evidence need with substantially less state and focus complexity.

### Connect the backend during Stage 18

Rejected by stage boundary. Stage 18 validates the shell and contracts; Stage 19
owns real runtime command-center integration.

## Consequences

- Later route content can integrate real endpoint payloads without rebuilding
  global navigation or layout.
- Status/maturity language is reusable before success-oriented screens exist.
- Initial JavaScript measures 102,802 bytes gzip, below the 256,000-byte limit.
- React Aria is the largest current dependency cost but supplies shared tabs and
  toggle behavior; optional graph/chart/data packages remain absent.
- Native routing is intentionally narrow and must be reconsidered if nested
  transitions, blockers, loaders, or complex route parsing appear.
- Dark-first styling still requires a future light-theme decision and full
  browser/assistive-technology validation.
