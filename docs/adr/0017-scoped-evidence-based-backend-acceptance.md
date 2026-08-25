# ADR-0017 — Scoped Evidence-Based Backend Acceptance

Status: Accepted  
Date: 2026-08-25

## Context

A single `tests passed` number cannot prove cancellation, process recovery,
resource pressure, chaos, security, the external API, or real inference all work.
Conversely, marking the backend failed until it becomes a production multi-user
service would contradict the approved single-user local project scope.

## Decision

Use two independent Stage 16 views:

1. Required categories receive binary PASS/FAIL against a versioned acceptance
   manifest. Every required category must pass for release-candidate status.
2. Subsystems receive `DONE`, `PARTIAL`, `FAILED`, or `DEFERRED` maturity labels.
   A known limitation cannot become `DONE` merely because its expected failure
   test passes.

The gate scope is the single-user loopback local backend on the measured RTX 3050
workstation. Acceptance recommends frontend eligibility but leaves authorization
pending explicit user approval. Remote/multi-user deployment remains deferred.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Test-count-only gate | Rejected | Does not prove required cross-subsystem behaviors or real API operation |
| Require every subsystem to be `DONE` | Rejected | Would conflate approved local scope with deferred production deployment and hide useful partial classifications |
| Manual checklist only | Rejected | Not reproducible or machine-verifiable |
| Binary requirements plus maturity classifications | Selected | Makes operational acceptance and technical debt simultaneously explicit |

## Consequences

- All required categories must pass; one failure rejects release-candidate status.
- The current candidate is accepted for recommendation while remaining overall
  `PARTIAL` due to persistence/fault, security, and model/evaluation limitations.
- Threshold changes are source changes and require a new retained gate run.
- The result does not automatically start frontend work.

## Evidence

- `configs/acceptance.json`
- `benchmarks/run_stage16_acceptance.py`
- `benchmarks/results/stage16-backend-acceptance-20260825T011603Z.json`
- `docs/backend-acceptance-report.md`
