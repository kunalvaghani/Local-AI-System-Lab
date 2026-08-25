# Stage 18 — Design System and UI Architecture

## Purpose

Translate the approved Stage 17 research into a recognizable design language,
navigable local application shell, reusable component contracts, and measurable
frontend foundation. Live backend integration remains Stage 19.

## Components and upgrades

| Component | Does | Upgrade |
| --- | --- | --- |
| Token system | Encodes color, type, spacing, surfaces, borders, motion, and density | Makes the research executable and reusable |
| Application route model | Defines twelve grouped URL-addressable areas | Turns backend domains into coherent information architecture |
| Application shell | Composes system bar, domain rail, work surface, and evidence pane | Gives every later screen the same inspection model |
| Resizable inspector | Lets pointer/keyboard users allocate workspace/evidence space | Supports dense investigation without arbitrary docking |
| Status language | Represents eleven operational/maturity states with glyph, text, and tone | Preserves failures, partial maturity, stale, and missing evidence |
| Density preference | Switches comfortable/compact tokens and stores one versioned preference | Supports both exploration and high-density work |
| Design-system route | Demonstrates foundations, states, and visualization rules interactively | Makes the stage observable, not documentation-only |
| Test/budget gates | Exercises behavior/accessibility and measures compressed JavaScript | Converts quality constraints into repeatable checks |

## Implemented behavior

- Twelve top-level routes navigate using native links and browser history.
- Back/forward and direct local route requests resolve through the Vite shell.
- The application adapts at 1100 px and 720 px layout boundaries.
- The evidence pane is pointer- and keyboard-resizable.
- Comfortable/compact density is selectable and stored locally with a versioned
  key.
- The design-system route exposes accessible tabs and every supported state.
- Every runtime domain displays its real future endpoint contract and an
  explicit not-requested state instead of fabricated telemetry.
- The development proxy is scoped to `/v1` on `127.0.0.1:8765`.

## Evidence

- Vite production build: PASS.
- Vitest/Testing Library component suite: 5/5 PASS.
- Axe-core primary-shell scan: zero automated violations with color contrast
  disabled because jsdom cannot compute rendered colors.
- Compressed initial JavaScript: 102,802 bytes against a 256,000-byte limit.
- Local deep route `/runtime`: HTTP 200.
- Existing Python acceptance classifier: retained and rerun at stage completion.
- No frontend API fetch, EventSource, mock runtime record, graph, chart, terminal,
  editor, or animation dependency is present.

## Limitations

- Automated axe output is not WCAG certification and did not evaluate computed
  color contrast.
- Visual breakpoint, forced-color, zoom, NVDA, and browser performance testing
  remain future acceptance work.
- Dark mode is the only visual theme.
- Native routing is intentionally shallow.
- No live backend data is visible until Stage 19.
