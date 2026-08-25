# Backend Acceptance Report — Stage 16

Date: 2026-08-25  
Release scope: single-user loopback local backend on the measured RTX 3050 workstation  
Machine evidence: `benchmarks/results/stage16-backend-acceptance-20260825T011603Z.json`

## Decision

**Release candidate: YES**  
**Overall classification: PARTIAL**  
**Gate recommendation: ACCEPT FOR SINGLE-USER LOOPBACK FRONTEND WORK WITH TRACKED LIMITATIONS**  
**Frontend authorization: PENDING EXPLICIT USER APPROVAL**

Every required Stage 16 verification category passed. `PARTIAL` is retained
because maturity classification is deliberately stricter than test success:
the terminal-state/output atomicity gap remains, only one real model backend is
installed and semantic evaluation is deferred, and security is application-level
rather than an OS sandbox or certification. None of these limitations is hidden
or relabelled as `DONE`.

## What Stage 16 is for

Stage 16 is the backend acceptance gate between implementation and frontend work.
It converts separate subsystem demonstrations into one reproducible verification
run, checks real inference against declared regression thresholds, and classifies
both required behavior and longer-term maturity. It adds no frontend code.

## Verification component roles and upgrades

| Component | What it does in Stage 16 | Upgrade over Stage 15 |
| --- | --- | --- |
| Acceptance manifest | Pins the release scope, minimum test count, expected chaos/security coverage, recovery requirement, and real-inference regression limits | Replaces informal acceptance with tracked pass/fail policy |
| Acceptance runner | Executes build, package, full/targeted tests, scheduler, hardware, recovery, trace, observability, chaos, security, and stub/real API workflows | Turns separate commands into one reproducible backend gate |
| Output hashing | Records SHA-256 of each command's stdout/stderr without retaining large or sensitive raw output | Provides evidence identity while keeping the retained report compact |
| Required-category evaluator | Produces explicit PASS/FAIL for every Stage 16 category | Prevents a broad test total from obscuring missing cancellation, recovery, security, or real-model evidence |
| Regression evaluator | Compares the real API run with the retained Stage 2 baseline and fixed resource/stream limits | Converts performance claims into declared, machine-checked thresholds |
| Maturity classifier | Assigns `DONE`, `PARTIAL`, `FAILED`, or `DEFERRED` per subsystem | Separates operational acceptance from production/multi-user maturity |
| Backend Acceptance Report | Explains evidence, limitations, and gate recommendation for people | Makes the release decision interview-defensible and reviewable |

## Tracked acceptance policy

| Check | Threshold |
| --- | ---: |
| Complete test suite | At least 150 tests |
| Security suite | 14 cases, zero failures, SQLite integrity `ok` |
| Chaos suite | 9 scenarios, 100% expected outcomes |
| Killed-process recovery | 100% successful safe-checkpoint recovery |
| Real generation speed | At least 75 tokens/second |
| TTFT regression from Stage 2 median | At most +50% |
| Peak child RAM | At most 1,600 MiB |
| VRAM delta | At most 1,500 MiB |
| Real API task-event stream | At most 10,000 ms |

These are acceptance limits for this measured local configuration, not universal
performance objectives for other hardware, models, or concurrency levels.

## Required verification results

| Required category | Result | Evidence |
| --- | --- | --- |
| Build and package | PASS | Compile and 0.16.0 package dry-run exited 0 |
| Unit and integration tests | PASS | 150 tests in 39.115 seconds |
| Edge cases, cancellation, timeouts | PASS | 8 targeted control tests plus complete suite |
| Malformed model output | PASS | 6 focused fault-adapter tests and chaos evidence |
| Scheduler behavior | PASS | FIFO `background → standard → interactive`; priority reverses priority order as expected |
| Persistence/restart/recovery | PASS | Killed worker recovered to `completed`, zero model calls, integrity `ok` |
| Resource pressure | PASS | Live `accept`; all six controlled admission actions demonstrated |
| Trace/replay | PASS | Integrity `ok`, replay `matched`, zero deterministic divergences |
| Observability | PASS | Four tasks, one recovery, 55 trace steps unified |
| Fault injection | PASS | 9/9 expected outcomes; recovery 1/1 |
| Security | PASS | 14/14 bounded cases, zero failures, integrity `ok` |
| Deterministic API | PASS | 16 operations, zero real model calls, integrity `ok` |
| Real-model API | PASS | 16 operations, one Qwen/llama.cpp call, integrity `ok` |
| Benchmark regression | PASS | All five declared thresholds passed |

## Real inference regression

| Measurement | Stage 2 median / limit | Stage 16 actual | Result |
| --- | ---: | ---: | --- |
| TTFT | 1,686.850 ms baseline; max +50% | 1,747.839 ms / +3.616% | PASS |
| Generation throughput | Minimum 75 tok/s | 93.68 tok/s | PASS |
| Peak child RAM | Maximum 1,600 MiB | 1,343.895 MiB | PASS |
| VRAM delta | Maximum 1,500 MiB | 1,189 MiB | PASS |
| HTTP/SSE task stream | Maximum 10,000 ms | 4,589.371 ms | PASS |

The one real task used Qwen2.5 1.5B, the direct llama.cpp completion backend,
and the admitted `performance` profile. Total inference was 2,375.728 ms. One
sample is regression acceptance evidence, not a statistically strong benchmark.

## Subsystem maturity classification

| Subsystem | Classification | Reason |
| --- | --- | --- |
| Core runtime | DONE | Build/package, complete suite, and targeted controls pass |
| Scheduler and resource admission | DONE | Ordering and all six admission outcomes pass |
| Tracing, replay, observability | DONE | Current local trace/telemetry scope passes |
| Backend API | DONE | Stub and real separate-process HTTP/SSE workflows pass |
| Persistence and recovery | PARTIAL | Safe killed-process recovery passes; terminal-state/output atomicity gap remains |
| Fault injection | PARTIAL | 9/9 expected outcomes, but containment remains 8/9 because the known database gap is reproduced |
| Security | PARTIAL | 14/14 bounded cases pass; no OS sandbox/certification claim |
| Model routing and evaluation | PARTIAL | Routing is explainable, but only one real backend exists and semantic evaluation is deferred |
| Remote multi-user deployment | DEFERRED | TLS, authentication, remote serving, and production HTTP infrastructure are outside scope |

## Known acceptance limitations

1. A fault between terminal-state commit and output persistence can leave a
   `completed` task with no output. The chaos suite detects this and does not
   claim containment.
2. Recovery is intentionally limited to explicit pre-invocation checkpoints;
   ambiguous model/tool side effects are not retried.
3. Only Qwen2.5 1.5B has a real installed backend. Controlled second-model routes
   are policy evidence, not multi-model inference evidence.
4. Output completion is not semantic correctness or quality evaluation.
5. Security is deterministic application policy around trusted local components,
   not a firewall, container, VM, penetration test, or certification.
6. The HTTP adapter is loopback development infrastructure without TLS,
   authentication, multi-user authorization, or global connection limits.
7. SQLite task content is not encrypted and has no automated retention or secure
   deletion policy.
8. The worktree contains accumulated uncommitted Stage 13–16 changes; the gate
   records the exact HEAD and dirty-entry count rather than claiming a clean tag.

## Acceptance conclusion

The backend is a reproducible release candidate for the declared single-user,
loopback, local-frontend scope. All mandatory Stage 16 categories passed and no
subsystem is `FAILED`. The tracked `PARTIAL` and `DEFERRED` classifications must
remain visible during frontend work and portfolio claims.

This report recommends acceptance, but it does not itself authorize Stage 17.
Frontend research begins only after explicit user approval.
