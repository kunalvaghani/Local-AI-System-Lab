# ADR-0023 — Server-catalogued, confirmed experiment UI

- Status: Accepted
- Date: 2026-08-25
- Stage: 23

## Context

The Stage 13 and Stage 14 CLIs already produced bounded chaos and adversarial
evidence, and Stage 15 exposed confirmed chaos execution plus retained security
results. The browser could not honestly discover the configured scenario list,
and it had no transport boundary for launching a fresh security suite. Copying
scenario names into the client would allow the UI and runtime policy to drift.

## Decision

The loopback service is the sole catalog owner. `GET /v1/chaos` reports the
configured fault scenarios, disabled-by-default state, per-run maximum, and
isolation contract; its existing confirmed `POST` remains synchronous and
isolated. `GET /v1/security` reports the deterministic case catalog and scope;
confirmed `POST /v1/security` executes only selected known cases in a unique
stub database and atomically retains the redacted JSON report. The existing
`GET /v1/security/results` returns the latest retained report.

The browser keeps scenario selection and confirmation ephemeral. It renders
expected versus actual propagation, containment, recovery, attack outcomes,
blocked-action evidence, integrity, duration, and real-model-call counts from
API payloads. PASS means the bounded defensive expectation held; it never means
the system is certified secure.

## Consequences

- Catalog changes appear in the UI without a client release or duplicated IDs.
- Both mutating experiment endpoints require literal confirmation and operate
  on separate deterministic runtimes/databases; the serving runtime is not armed.
- Security execution now creates a retained local evidence file and can occupy
  one standard-library HTTP worker while the synchronous suite runs.
- Repeating a confirmed request repeats the experiment; there is no idempotency
  key, campaign scheduler, authentication, or remote-use claim.
- The known terminal-result atomicity gap remains visible as a containment
  failure rather than being relabelled as success.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Hard-code catalogs in React | Rejected | Configuration and UI can drift |
| Display retained terminal output only | Rejected | Does not provide controlled interactive execution |
| Run faults in the serving runtime | Rejected | Violates the accepted isolation boundary |
| Treat 14/14 as security certification | Rejected | Bounded deterministic regression evidence is not penetration testing |
| Add background campaigns or queues | Deferred | Stage 23 requires controlled local runs, not orchestration infrastructure |

## Evidence

- `tests/test_api.py`
- `apps/web/src/App.test.tsx`
- `apps/web/scripts/stage23-smoke.mjs`
- `benchmarks/results/stage23-chaos-security-20260825T143324Z.json`
