# ADR-0012: Hash-chained task traces and bounded replay

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 10 durably stored lifecycle events and execution steps but did not bind
them into runs, detect payload tampering, identify deterministic boundaries, or
support meaningful replay/comparison. Re-running model generation or tool calls
would be misleading or unsafe.

## Decision

Migrate SQLite forward from schema v1 to v2. Create one trace run per task,
ordered trace steps, and persisted replay reports. Each step carries a stable
UUIDv5 derived from run/ordinal/event, actor/component, timestamp, raw canonical
input/output hashes, a normalized semantic hash, state/model/configuration/failure
metadata, the preceding hash, and a SHA-256 envelope hash.

Classify steps as deterministic, nondeterministic, observational, or
side-effecting. Replay verifies payload and envelope hashes plus chain continuity,
then applies only the deterministic state-transition reducer. Model generation
and hardware/scheduler observations are inspected but not regenerated. Tool
side effects are skipped. Cross-run comparison aligns event occurrences and
compares normalized semantic hashes only for deterministic steps.

## Consequences

- A stored run can be loaded after restart and inspected as one ordered trace.
- Modified trace payloads fail replay integrity checks.
- Deterministic orchestration can be reconstructed and compared without claiming
  byte-identical model generation.
- Stable IDs are stable inside a run; separate runs intentionally have different IDs.
- SHA-256 integrity is tamper-evidence, not authentication against an attacker
  who can rewrite both rows and hashes.
- Trace payloads increase database size and may retain sensitive local inputs;
  redaction/retention/export policy remains future work.

## Alternatives considered

- Replay the entire runtime including model/tools: rejected because generation is
  nondeterministic and tool side effects may duplicate.
- Store only hashes: rejected for the local debugging goal because deterministic
  state reconstruction needs structured evidence.
- Store only raw events without a chain: rejected because row mutation/reordering
  would not be detected by replay.
- Introduce OpenTelemetry now: deferred to Stage 12 because Stage 11 needs an
  inspectable local execution contract before an observability/export layer.
