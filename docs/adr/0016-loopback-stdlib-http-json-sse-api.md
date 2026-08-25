# ADR-0016 — Loopback Standard-Library HTTP/JSON and SSE API

Status: Accepted  
Date: 2026-08-25

## Context

Stage 15 must make the complete local runtime operable by a future frontend
without direct Python calls. The transport must support ordinary request/response
inspection plus incremental task lifecycle delivery. It must remain inspectable,
free, local, and dependency-light, while preserving the Stage 14 security and
Stage 13 explicit-arming boundaries.

## Decision

Use a versioned loopback HTTP/1.1 API with UTF-8 JSON responses and Server-Sent
Events (SSE) for task lifecycle streams. Implement the adapter with Python's
`ThreadingHTTPServer`; keep all transport-independent operations in
`RuntimeApiService` and bounded asynchronous ownership in `ApiTaskManager`.

The server accepts literal loopback addresses only. JSON objects reject duplicate
keys, non-finite values, unknown fields, excessive body size, invalid encodings,
and out-of-range timeouts before they cross runtime boundaries. Responses use a
stable data/error envelope and security/no-store headers. The adapter does not
serve files, add CORS, expose system prompts, or return raw trace payloads.

Chaos requests require literal `confirm=true`, accept at most three unique named
scenarios, and execute through a fresh stub runtime and unique SQLite database.
They cannot arm the serving runtime.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| FastAPI/Starlette | Deferred | Excellent validation/OpenAPI ecosystem, but Stage 15 needs no third-party dependency for the bounded local contract and core logic must stay framework-independent |
| WebSocket | Rejected for current scope | Bidirectional frames add protocol/state complexity; commands remain ordinary HTTP and execution updates are server-to-client only |
| gRPC | Rejected for current scope | Strong schemas and streaming, but generated clients/HTTP2 add tooling cost before a multi-language or remote-service requirement exists |
| Polling only | Rejected | Cannot demonstrate a genuine streamed execution interface and adds repeated request overhead |
| Standard-library HTTP + JSON + SSE | Selected | Directly testable over a real socket, dependency-free, sufficient for a loopback future frontend, and easy to replace because service logic is transport-independent |

JSON follows RFC 8259's interoperable object/number/string model. SSE uses the
standard `text/event-stream` event format. Python explicitly warns that
`http.server` is not recommended for production; therefore this decision is a
loopback development interface, not an internet-facing production server.

## Consequences

- The future frontend can create, inspect, cancel, and stream tasks and inspect
  every major backend subsystem through `/v1`.
- Existing runtime protocols and factories remain independent of HTTP.
- One server process may accept multiple HTTP requests, while the task manager
  caps in-flight submissions and the existing scheduler/inference guards remain
  authoritative.
- SSE reconnect cursors are process-local for active API-owned tasks. Durable
  completed tasks remain inspectable after restart, but active task resumption
  across API-process failure is not promised.
- Authentication, TLS, reverse-proxy hardening, multi-user authorization, rate
  limiting by identity, and production ASGI deployment are deferred. Binding to
  a non-loopback address is rejected.

## Evidence

- `tests/test_api.py` exercises the real socket contract, SSE, cancellation,
  malformed requests, security boundaries, redacted trace replay, isolated
  chaos, and retained security evidence.
- `benchmarks/results/stage15-api-20260824T205654Z.json` records 16 external
  operations from a separate client process, zero post-launch direct runtime
  calls, zero real LLM calls, completed durable state, 15 SSE lifecycle events,
  16 redacted trace steps, valid replay, expected chaos outcome, zero retained
  security failures, and SQLite integrity `ok`.
- `benchmarks/results/stage15-api-real-20260825T010429Z.json` repeats the complete
  external workflow through one guarded Qwen2.5 1.5B/llama.cpp call and retains
  measured inference, SSE, trace/replay, chaos, security, and integrity evidence.

## References

- [RFC 8259 — The JavaScript Object Notation Data Interchange Format](https://www.rfc-editor.org/info/rfc8259/)
- [WHATWG — Server-sent events](https://html.spec.whatwg.org/dev/server-sent-events.html)
- [Python `http.server` documentation and production warning](https://docs.python.org/3.12/library/http.server.html)
