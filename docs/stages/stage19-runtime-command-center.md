# Stage 19 — Runtime Command Center

## Purpose

Connect the Stage 18 browser shell to the accepted loopback API so a user can
observe the live runtime, launch a bounded task, follow its ordered lifecycle,
inspect truthful output/measurements, and request cancellation from one local
control surface.

## Components and upgrades

| Component | Does | Stage 19 upgrade |
| --- | --- | --- |
| Typed API client | Unwraps versioned envelopes and preserves request errors/IDs | Replaces endpoint placeholders with real transport contracts |
| Query provider | Deduplicates, cancels, retries, polls, and invalidates server state | Gives six independent inspection resources explicit ownership |
| Global connection indicator | Polls `/v1/health` | Replaces the Stage 18 prototype status with real API availability |
| Runtime pulse | Shows runtime, queue, selected model, RAM, VRAM, and task evidence | Makes the backend's current operating state directly inspectable |
| Task composer | Selects a real agent/workload and posts a bounded objective | Adds controlled execution from the browser without expanding authority |
| URL task selection | Stores the selected task as `?task=<id>` | Makes task evidence refreshable without browser data persistence |
| Task inspector | Polls status and shows durable state, output, error, and inference fields | Preserves missing measurements as unavailable instead of zero |
| SSE lifecycle adapter | Follows ordered task events, reconnects by cursor, and closes terminal streams | Adds live execution evidence with a 200-event client bound |
| Cancellation control | Sends the existing task DELETE contract and reconciles caches | Extends browser control to cooperative cancellation |
| Live smoke runner | Exercises `/runtime`, proxy inspection, task creation, SSE, and terminal inspection | Retains reproducible end-to-end Stage 19 evidence |

## Implemented behavior

- Health polls every three seconds; scheduler every second; hardware and metrics
  every five seconds; agents and models every sixty seconds.
- Independent inspection queries start in parallel and use abort signals.
- Task objectives are limited to 4,096 characters and use the backend's 30-second
  execution limit and interactive/standard/background workload classes.
- Selected task IDs are validated, URL-addressable, and never persisted locally.
- SSE events are deduplicated by event ID/type, bounded to 200, displayed as an
  ordered text rail, and reconnected after a continuing stream timeout.
- Terminal task snapshots update the query cache, close the stream, and refresh
  runtime evidence.
- API failures show the backend message and request ID when available.
- Stub output explicitly retains `real_llm_calls: 0`; null inference fields remain
  `Unavailable` while a measured zero total remains `0 ms`.

## Evidence

- Real `/runtime` request through Vite: HTTP 200.
- Real `/v1` proxy health: `ok`, runtime `running`.
- Retained smoke result: `stage19-runtime-command-center-20260825T121824Z.json`.
- Real proxy task: HTTP 202, terminal `completed`, durable `completed`, zero real
  LLM calls, 15 lifecycle events, one task snapshot, and one end event.
- Smoke stream: 632.633 ms; complete smoke: 967 ms. These are one-run local
  integration timings, not throughput or user-interaction claims.
- Frontend component suite: 7/7 pass, including task launch, URL selection,
  lifecycle rendering, cancellation, truthful unavailable evidence, navigation,
  preferences, and automated axe checks.
- Production build: 389.17 kB raw/119.14 kB Vite-reported gzip JavaScript and
  21.80 kB raw/4.66 kB gzip CSS; build completed in 209 ms.
- Exact bundle gate: 117,956 gzip JavaScript bytes versus 256,000 maximum,
  +15,154 bytes (+14.7%) from Stage 18.
- Existing Python backend regression suite: 150/150 pass in 38.816 seconds.

## Limitations

- The deterministic development composition runs no real LLM. The UI exposes
  that fact; retained Stage 16 evidence remains the real-model acceptance source.
- The backend has no list-all-tasks endpoint, so Stage 19 inspects the selected
  created/known task rather than inventing a task history.
- Event virtualization and rich scheduler/trace graphs remain later work.
- Active task ownership and SSE cursors remain process-local across API restart.
- On Windows, aborting concurrent polling during HMR or process teardown can
  produce noisy `ConnectionAbortedError` tracebacks in the standard-library
  development server even though the client and server terminate correctly.
- No real-browser interaction timing, computed contrast, 400% zoom,
  forced-colors, or screen-reader matrix is claimed.
