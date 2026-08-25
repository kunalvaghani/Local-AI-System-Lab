# Stage 16 — Backend Verification & Acceptance Gate

## Purpose

Stage 16 verifies the complete backend as one release candidate before any
frontend phase begins. It adds a tracked acceptance policy, one orchestration
command, retained machine evidence, and the human-readable
[Backend Acceptance Report](../backend-acceptance-report.md).

## New capability

Run the entire backend gate:

```powershell
python -m benchmarks.run_stage16_acceptance
```

The command exits zero only when every mandatory category passes. It launches
the real local model once, performs no paid or hosted calls, records hashes rather
than retaining large command output, and emits one JSON classification artifact.

## Component upgrade map

| Component | Stage 16 responsibility | Upgrade |
| --- | --- | --- |
| `configs/acceptance.json` | Versioned scope and pass/fail thresholds | Makes the gate reproducible instead of judgment-only |
| `run_stage16_acceptance.py` | Executes and summarizes fourteen verification commands | Integrates every backend subsystem into one acceptance run |
| Required-category matrix | PASS/FAIL for all master-prompt categories | Makes missing evidence visible |
| Maturity matrix | `DONE`/`PARTIAL`/`FAILED`/`DEFERRED` | Preserves known debt even when required checks pass |
| Retained JSON | Timings, hashes, summaries, thresholds, regression math, decision | Gives machine-verifiable evidence for the release candidate |
| Acceptance report | Explains scope, results, limits, and recommendation | Gives reviewers an honest human decision record |

## Result

- 14/14 mandatory categories: PASS.
- 14/14 orchestration commands: exit 0.
- Complete suite: 150 tests passed in 39.115 seconds.
- Real API: 16 operations, one Qwen/llama.cpp call, SQLite integrity `ok`.
- Benchmark checks: 5/5 PASS.
- Failed subsystems: zero.
- Overall maturity: `PARTIAL`.
- Release candidate: yes.
- Recommendation: accept for single-user loopback frontend work with tracked limitations.
- Frontend authorization: pending explicit user approval.

## Stopping point

Stage 16 is complete. Stage 17 frontend research has not started, and no frontend
files or production UI code were created.
