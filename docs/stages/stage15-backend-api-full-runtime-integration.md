# Stage 15 — Backend API & Full Runtime Integration

## What this stage is for

Stage 15 turns the complete local runtime into an externally operable backend.
A caller now uses a documented loopback HTTP contract instead of importing and
calling runtime Python objects. This is the final implementation stage before
the Stage 16 backend verification and acceptance gate; it does not add a frontend.

## Component purpose and upgrade

| Component | What it does | Upgrade over Stage 14 |
| --- | --- | --- |
| `ApiConfig` | Strictly validates loopback bind, ports, request/task/stream limits, chaos selection cap, and retained-result directory | Makes the external boundary explicit and bounded in tracked configuration |
| `RuntimeApiService` | Maps versioned operations to runtime tasks, agents, scheduler, hardware, registry, metrics, traces, replay, chaos, and security evidence | Integrates every completed backend subsystem behind one transport-independent service |
| `ApiTaskManager` | Owns accepted task records, a bounded in-flight semaphore, worker threads, cooperative cancellation, terminal status, durable fallback inspection, and shutdown | Converts the synchronous caller API into externally controllable asynchronous work without changing core orchestration |
| HTTP adapter | Serves `/v1` JSON over a real loopback socket; validates media type, UTF-8, duplicate keys, fields, limits, queries, and methods; maps typed errors to HTTP status | Establishes a stable frontend-facing protocol while preserving core framework independence |
| SSE stream | Emits ordered lifecycle events, a terminal task snapshot, and an explicit end reason using `text/event-stream` | Makes active execution observable without polling or WebSocket complexity |
| Safe inspection views | Expose agents, scheduler, hardware, models/budgets, observability, traces, and replay | Omits system prompts, absolute model paths, trace input/output payloads, and run metadata at the API boundary |
| Chaos endpoint | Requires exact confirmation and runs selected scenarios in an isolated stub runtime/unique database | Makes reliability experiments externally launchable without arming or corrupting the serving runtime |
| Security-results endpoint | Returns the newest retained Stage 14 result with an explicit scope disclaimer | Makes bounded adversarial evidence inspectable without claiming certification |
| OpenAPI document and CLI | Documents the routes and launches real/stub API compositions through `local-ai-api` | Provides a reproducible backend entry point for Stage 16 and the later frontend |
| External benchmark | Launches the API in a child process and performs all operations through HTTP/SSE | Proves the new capability with zero direct runtime calls after process launch |

## Protocol contract

The base URL is `http://127.0.0.1:8765/v1`. Successful JSON responses use
`{"data": ..., "request_id": ...}`; expected errors use
`{"error": {"code", "message", "details"}, "request_id": ...}`.

| Method | Route | Capability |
| --- | --- | --- |
| GET | `/v1`, `/v1/health`, `/v1/openapi.json` | Discovery, health/integrity, contract |
| POST | `/v1/tasks` | Create bounded asynchronous agent task |
| GET / DELETE | `/v1/tasks/{task_id}` | Inspect or cooperatively cancel task |
| GET | `/v1/tasks/{task_id}/events` | Stream lifecycle and terminal state over SSE |
| GET | `/v1/tasks/{task_id}/trace` | Retrieve hash/integrity trace without raw payloads |
| GET | `/v1/agents`, `/scheduler`, `/hardware`, `/models`, `/metrics` | Inspect integrated runtime components |
| GET / POST | `/v1/traces/{run_id}`, `/v1/traces/{run_id}/replay` | Inspect and deterministically replay trace reducers |
| POST | `/v1/chaos` | Launch explicitly confirmed isolated scenarios |
| GET | `/v1/security/results` | Inspect retained bounded security evidence |

## Run and demonstrate

Start a deterministic API with no real LLM calls:

```powershell
python -m runtime.api_cli --stub
```

Start the complete real Qwen/llama.cpp runtime:

```powershell
python -m runtime.api_cli
```

Run the independent-process external demonstration:

```powershell
python -m benchmarks.run_stage15_api
```

## Evidence

The retained `stage15-api-20260824T205654Z.json` passed all asserted operations:

- 16 HTTP/SSE operations from a separate client process;
- zero direct runtime calls after launch and zero real LLM calls;
- task `completed` with durable state `completed`;
- 15 streamed lifecycle events plus terminal task/end events;
- two safe agent views, FIFO scheduler state, source-labelled live hardware,
  two registry entries, and one task in unified metrics;
- 16 trace steps with raw payloads omitted and replay integrity valid;
- unconfirmed chaos rejected and confirmed model-timeout outcome matched in isolation;
- retained security report contained zero failed cases;
- serving database integrity `ok`.

The retained `stage15-api-real-20260825T010429Z.json` then repeated the same
16-operation external workflow against the real guarded runtime. Qwen2.5 1.5B
completed one llama.cpp call through HTTP/SSE using the admitted `performance`
profile: 2,973.505 ms total inference, 2,210.807 ms TTFT, 103.32 tokens/second,
1,343.887 MiB peak child RAM, and 1,189 MiB VRAM delta. The stream contained 18
lifecycle events and its redacted trace contained 19 steps; replay, isolated
chaos, retained security evidence, and database integrity all passed.

The nine focused Stage 15 tests cover strict loopback/config validation,
discovery/health/OpenAPI/no static files, task creation/inspection/SSE, safe
component views, redacted trace replay,
strict transport and security rejection, isolated chaos/security retrieval, and
cooperative cancellation plus durable inspection after API restart.

## Known limits

- Python's standard-library HTTP server is intentionally loopback-only and not a
  production internet server. There is no TLS, authentication, user isolation,
  reverse-proxy trust model, or identity-based rate limiting.
- Accepted tasks and SSE cursors are process-local. Completed durable tasks can
  be inspected after restart; automatic continuation of arbitrary active API
  tasks remains constrained by the existing safe checkpoint contract.
- Task objectives, inputs, and outputs remain in the ignored local SQLite store.
  The API hides raw trace payloads, but encryption, retention, deletion, and
  export policy are still technical debt.
- `ThreadingHTTPServer` uses one handler thread per connection; API task capacity,
  scheduler capacity, inference process limits, and stream deadlines bound the
  demonstrated path but do not constitute hostile-client isolation.
- The retained results include both deterministic protocol evidence and one real
  Qwen API run. The real run is a single integration sample, not a statistically
  strong performance or output-quality claim; Stage 16 must perform the full
  integrated acceptance and regression classification.

## Stopping point

Stage 15 is complete. Stage 16 backend verification has not started, and frontend
implementation remains prohibited until that gate is completed and approved.
