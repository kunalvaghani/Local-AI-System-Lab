# Current Project State

## Active Project

Local AI Systems Lab — a fully local, inspectable AI runtime/platform for constrained consumer hardware.

## Current Milestone

Durable and live runtime evidence now converges in one windowed, machine-readable
observability report with task/activity totals, sample-aware distributions,
recent task drill-down, and source-labelled scheduler/hardware snapshots; waiting
at the Stage 12 approval gate.

## Current Stage

Stage 12 — Observability & Metrics Backend — COMPLETE, AWAITING APPROVAL.

## Current Subsystem

Windowed SQLite telemetry queries, unified aggregation/distributions, live
scheduler/hardware snapshots, recent task/event drill-down, and JSON reporting.

## Last Completed Work

- Added a typed `ObservabilityBackend` and Stage 12 real/stub factory composition without changing SQLite schema v2.
- Added one consistent windowed SQLite read transaction across task state, metric events, outputs, tool calls, recovery attempts, traces, and replay reports.
- Added task/activity totals and count/min/P50/P95/max/mean distributions for task, queue, scheduler, tool, recovery, inference, TTFT, throughput, RAM, and VRAM evidence.
- Added bounded recent-task/event drill-down connecting run, agent, model, route, scheduler, hardware, failure, recovery, and trace evidence.
- Added optional live scheduler and source/confidence-labelled hardware snapshots; unavailable samples remain `null` with count zero.
- Defined reported retries truthfully as recovery attempts because no independent generic retry subsystem exists.
- Retained `stage12-observability-20260824T163054Z.json`: four tasks, three completions, one expected failure, two model calls, one tool call, one recovery/retry, four trace runs, and 55 trace steps.
- Ran real Stage 12 Qwen inference and queried it after restart: one completed task/model call/route, 18 trace steps, 2,927.102 ms total, 2,238.325 ms TTFT, 96.16 tok/s, 1,343.703 MiB RAM, and 1,189 MiB VRAM.
- Added `local-ai-observe`, Stage 12 runner, ADR-0013, Stage 12 report, and 9 focused observability tests.

- Migrated SQLite forward from schema v1 to v2 with trace runs, ordered trace steps, and persisted replay reports.
- Added stable per-run UUID step identities, UTC timestamps, actor/component ownership, canonical input/output hashes, normalized semantic hashes, state/model/configuration/failure metadata, and previous/envelope hashes.
- Classified each traced event as deterministic, nondeterministic, observational, or side-effecting.
- Added hashed model prompt/configuration/output boundaries while explicitly classifying generation as nondeterministic.
- Added side-effect-free replay that verifies the full trace chain and reconstructs legal state transitions without new model calls or repeated tool operations.
- Added cross-run comparison with deterministic matches/divergences, nondeterministic observations, missing events, and model/configuration equality.
- Added trace loading after restart plus CLI `demo`, `inspect`, `replay`, and `compare` operations.
- Retained `stage11-trace-replay-20260824T143744Z.json`: two 15-step runs, 10 deterministic matches, zero divergences, five nondeterministic observations, replay state `completed`, integrity `ok`.
- Ran real Stage 11 Qwen inference and replay: 18 trace steps, 11 deterministic matches, seven observed-only steps, reconstructed `completed`, no regeneration, integrity `ok`.
- Added `local-ai-trace`, Stage 11 runner, ADR-0012, Stage 11 report, and 9 focused tracing tests.

- Added SQLite schema version 1 for agents, tasks, state transitions, checkpoints, lifecycle events, metric events, execution steps, model configurations, tool calls, outputs, and recovery attempts.
- Added validated persistence configuration with foreign keys, 5,000 ms busy timeout, WAL journaling, and `FULL` synchronous durability.
- Added narrow SQLite agent, lifecycle, metric, checkpoint, and task-state adapters over one shared runtime store.
- Kept the Stage 4 legal graph authoritative and added explicit `RECOVERING -> PLANNING`; illegal SQLite transitions roll back without partial state.
- Added explicit `recovery_ready` checkpoints only in `PLANNING`, before model/tool invocation begins.
- Added recovery classification for recoverable, terminal, unsafe in-flight, and invalid-checkpoint tasks.
- Added a durable recovery-attempt ledger and refused automatic retries for terminal or ambiguous side-effect boundaries.
- Persisted model configuration at runtime start, tool requests/results/errors, inference/tool outputs, and task/event timestamps.
- Demonstrated an actual worker process killed after its committed checkpoint and a fresh runtime completing the original task through `RECOVERING`.
- Retained `stage10-recovery-20260824T131728Z.json` with schema version, row counts, state history, output, and `integrity_check: ok`.
- Ran real Stage 10 Qwen inference and reconstructed its completed state/five transitions from SQLite without starting the model.
- Added `local-ai-recovery`/`runtime.recovery_cli`, Stage 10 runner, ADR-0011, Stage 10 report, and 11 focused tests.

- Added a typed, versioned registry for model identity, artifact/backend availability, capabilities, token limits, minimum memory, latency class, quality rank, and benchmark provenance.
- Registered the installed Qwen2.5 1.5B baseline and an explicitly unavailable/unbenchmarked optional Qwen2.5 0.5B candidate without fabricating a second real local artifact.
- Added an explainable workload router using task type, complexity, context/output size, latency, queue depth, live memory, task budgets, and historical benchmark evidence.
- Retained every candidate acceptance/rejection and scoring reason in route lifecycle/result evidence.
- Added interactive, standard, and background compute-budget defaults covering maximum inference calls, generated tokens, total time, RAM, and VRAM.
- Enforced zero-call rejection, native token capping, remaining-time scheduler capping, and exact-profile estimated RAM/VRAM limits before scheduler submission.
- Demonstrated a 600 MiB VRAM budget automatically skipping larger profiles and selecting the admitted `constrained` profile.
- Added post-execution usage evidence for calls, generated token runs, elapsed time, peak child RAM, and VRAM delta.
- Demonstrated controlled interactive explanation routing to the compact candidate and standard risk analysis routing to the 1.5B model for an exact capability reason.
- Demonstrated truthful live routing to the only installed/configured model, with the compact candidate rejected for missing artifact/backend.
- Ran real interactive and background Stage 9 Qwen executions, including different profile and token-budget choices.
- Added `local-ai-routing`/`runtime.routing_cli`, a retained Stage 9 route result, ADR-0010, Stage 9 report, and focused tests.

- Added four typed, tracked inference profiles controlling context, batch/ubatch, generation/batch threads, GPU layers, flash attention, and device selection.
- Preserved the exact Stage 7 configuration as `performance`; labelled every alternative an experimental hypothesis rather than an optimum.
- Added workload-specific profile order: interactive/standard prefer performance, while background prefers balanced.
- Added `AdaptiveInferenceController`, which captures one fresh snapshot, evaluates candidates in order, and selects only the first profile receiving `ACCEPT`.
- Reuses Stage 7 estimation/admission for every candidate; a recommendation never bypasses re-admission or reaches native inference directly.
- Added request-scoped llama.cpp flags for all seven controlled parameters while retaining `--fit off`.
- Added lifecycle/result evidence for every attempted profile, exact selected/applied profile, hardware snapshot, admission, reason, scheduler, and inference metrics.
- Demonstrated controlled pressure selecting balanced after performance queued, missing GPU selecting CPU-safe, and missing RAM blocking all work before the scheduler.
- Ran the same real workload through performance, balanced, constrained, and CPU-safe profiles and retained the raw JSON result.
- Demonstrated live standard selecting performance and live background selecting balanced through the full agent runtime.
- Added `local-ai-adaptive`/`runtime.adaptive_cli`, Stage 8 benchmark runner, ADR-0009, and Stage 8 report.

- Added source/confidence-labeled CPU identity, logical processor, RAM capacity/availability, GPU, VRAM pressure, utilization, temperature, driver, and compute-capability profiling.
- Preserved unavailable physical-core evidence as `null` with a warning rather than fabricating it from the 16 logical processors.
- Added validated model metadata from the actual 1,117,320,736-byte pinned GGUF file and explicit estimator coefficients/reserves.
- Added a transparent host/VRAM estimator with component-level arithmetic, assumptions, and medium/low confidence labels.
- Compared the exact baseline prediction against the retained real Stage 6 peak: RAM +122.643 MiB/+9.158%; VRAM +17.116 MiB/+1.404%.
- Added inspectable `ACCEPT`, `QUEUE`, `REDUCE_CONTEXT`, `REDUCE_GPU_OFFLOAD`, `FALLBACK`, and `REJECT_UNSAFE` decisions.
- Added a pre-scheduler admission gate: only `ACCEPT` invokes the scheduler/backend; other outcomes raise structured `admission_controlled` and enter terminal `RESOURCE_BLOCKED`.
- Added `local-ai-hardware`/`runtime.hardware_cli`, controlled coverage of all six branches, ADR-0008, and the Stage 7 report.

- Added typed scheduler policies, workload classes, priorities, request statuses, options, handles, results, snapshots, and aggregate metrics.
- Added `QueuedScheduler` with configurable bounded workers and stable FIFO or priority selection.
- Added interactive, standard, and background default priorities of 100, 50, and 10 with explicit priority override support.
- Added wait-time aging plus an oldest-request maximum-wait promotion to prevent indefinite background starvation while workers make progress.
- Added an independent queue monitor so queued cancellation and expiry occur even while all workers are busy.
- Added end-to-end deadlines spanning queue wait and operation execution; active expiry signals the cooperative backend token.
- Added cancellation for queued and running logical requests and mapped scheduler cancellation/timeout to `CANCELLED`/`TIMEOUT` task states.
- Added queue metrics for current/running/peak depth, outcomes, P50/P95/max wait, execution order, and starvation promotions.
- Routed real `AgentRuntime` inference through one priority worker, matching the current backend's single-process limit.
- Added scheduler request lifecycle events and per-result request ID, workload, priority, queue wait, execution time, status, and timestamps.
- Extended inference `generate()` with cancellation so scheduler control reaches the owned llama.cpp process.
- Added locks to process-local agent, event, checkpoint, and metric stores for concurrent Stage 6 callers.
- Demonstrated the same submissions as FIFO `background -> standard -> interactive` and priority `interactive -> standard -> background`.
- Demonstrated a real Technical Explainer/Qwen run through the Stage 6 scheduler.
- Added the `local-ai-scheduler`/`runtime.scheduler_cli` comparison, ADR-0007, Stage 6 report, and ordering/control/concurrency tests.

## Currently Working On

None. Stage 12 is complete and work is stopped at the mandatory approval gate.

## Current Blockers

- User approval is required before Stage 13.
- No technical blocker remains for the demonstrated Stage 12 observability path.
- A second real model artifact/backend is not installed; controlled route differences are therefore policy evidence, not a claim of compact-model inference.

## Important Decisions

- Follow one stage at a time and stop for explicit approval after each stage.
- Keep Stage 12 pull-based and local: query authoritative SQLite evidence, then attach separately labelled live scheduler/hardware snapshots.
- Preserve missing observations as null statistics with zero sample count; never turn an absent measurement into a zero.
- Define retries as recovery attempts until a distinct retry subsystem exists, and disclose that source in every report.
- Keep SQLite schema v2; aggregation does not justify duplicating authoritative records on the write path.
- Treat one task as one durable trace run; recovery continues that run rather than fabricating a new task history.
- Derive stable step identity from run ID, ordinal, and event name; use canonical hashes plus a previous-hash chain to detect mutation/reordering.
- Replay only deterministic reducers. Observe model/environment evidence and skip tool side effects instead of claiming full behavioral re-execution.
- Compare normalized semantic hashes only for deterministic steps; report nondeterministic evidence separately.
- Treat SHA-256 chains as tamper-evidence, not authentication against an actor who can recompute the database.
- Use explicit JSON and typed reconstruction; never persist runtime objects with pickle.
- Treat the existing legal state graph as authoritative inside SQLite transactions.
- Automatically retry only an exact pre-invocation `recovery_ready` checkpoint; never guess whether model/tool side effects occurred.
- Record `RECOVERING` and recovery attempts durably instead of disguising recovery as a fresh task.
- Reject terminal and in-flight tasks from automatic recovery, preserving them for inspection/manual resolution.
- Use SQLite WAL/FULL with short per-operation connections for the current single-host runtime.
- Define model availability as both artifact presence and configured backend support; aliases and stubs are not counted as real models.
- Retain unavailable candidates and their rejection reasons instead of silently dropping them from route evidence.
- Treat declared capabilities/quality ranks as routing policy metadata, not semantic output-quality proof.
- Enforce call/token/time and estimated memory limits before scheduler submission; report observed peaks separately because sampling cannot retroactively prevent an estimator miss.
- Keep the existing exact-profile admission as the final safety authority after routing.
- Complete and accept the backend before production frontend work.
- Keep important runtime logic framework-independent and inspectable.
- Use Python as the initial implementation language; require measured evidence before introducing C++.
- Treat observed repository state and executed tests as higher-confidence evidence than plans.
- Use Python structural protocols and constructor injection for current component boundaries.
- Keep Stage 1 synchronous and dependency-free until real inference/scheduling requirements provide evidence for async or third-party tooling.
- Use the direct, pinned llama.cpp subprocess path as the first serious baseline; keep Ollama outside this measurement.
- Launch one native process per request in Stage 2 to make streaming, cancellation, cleanup, and cold-load cost explicit.
- Allow only one active inference process per backend instance until scheduler admission/concurrency is implemented.
- Keep all runtime inference offline; permit network access only in the explicit setup/download workflow.
- Resolve specialized agents by registered stable identity; callers do not construct direct backend calls.
- Treat tool capabilities as explicit narrow grants; a name and its required permission set must both match a registered definition.
- Use only coarse direct task states in Stage 3; reserve detailed states, failure variants, and legal-transition enforcement for Stage 4.
- Store lifecycle events separately from performance telemetry; Stage 10 retains both through narrow SQLite adapters.
- Treat task completion and role/output correctness as separate concerns.
- Keep every state change behind the `TaskStateMachine` protocol; runtime branches cannot assign current state directly.
- Treat all failure and completed states as terminal and non-reentrant.
- Record an initialization transition (`None -> CREATED`) so task history is complete from origin.
- Route tool-only success through `WAITING_FOR_TOOL -> VALIDATING -> COMPLETED`; never bypass the shared state machine.
- Keep tool-handler and scheduler request deadlines separate; both are enforced at their owning execution boundaries.
- Permit only vetted, read-only tools under application-level containment; do not claim this is an OS sandbox.
- Use cooperative cancellation tokens for tools and return at the configured deadline; require process isolation before admitting untrusted or side-effecting handlers.
- Default deny a tool unless the executing agent has an exact grant with all required permissions.
- Keep FIFO as an executable baseline and use aged priority for the current serious runtime.
- Use stable sequence ordering for equal effective priorities.
- Treat interactive/standard/background values 100/50/10 as transparent baselines, not measured optima.
- Count the request deadline from submission so queue time cannot escape the budget.
- Run an independent queue monitor so a busy worker cannot prevent queued timeout/cancellation.
- Keep one real scheduler worker; Stage 7 establishes per-request fit but does not prove concurrent inference safe.
- Preserve synchronous `AgentRuntime.run()` for now while the scheduler itself exposes request handles; external async control belongs to the API stage.
- Record scheduler queue evidence in task results and lifecycle metrics without claiming Stage 12 observability.
- Reject only empty output in Stage 4; semantic validators remain future work.
- Attach sources and confidence to resource evidence; never substitute declared hardware for an unavailable live reading.
- Keep estimator arithmetic and safety reserves explicit; treat one exact configuration as medium-confidence and extrapolation as low-confidence.
- Execute only `ACCEPT` in Stage 7. Recommendations require re-evaluation after Stage 8/9 applies a change or pressure clears.
- Distinguish pre-execution `RESOURCE_BLOCKED` from a backend `OUT_OF_MEMORY` failure.
- Use discrete tracked profiles instead of unconstrained runtime parameter mutation.
- Share one fresh hardware snapshot across all candidate attempts so selection compares a coherent pressure point.
- Require `ACCEPT` for the exact selected context/GPU-layer profile before scheduler submission.
- Keep llama.cpp `--fit off`; native code must not silently override the controller's inspectable decision.
- Treat current profile values and workload order as measured policy baselines, never universal optima.
- Keep adaptive profiles model-specific; Stage 9 routes models first and requires a real backend/profile/admission bundle before a second model becomes executable.

See [ADR-0001](docs/adr/0001-stage-gated-modular-backend-first.md), [ADR-0002](docs/adr/0002-typed-protocols-and-stdlib-skeleton.md), [ADR-0003](docs/adr/0003-pinned-llama-cpp-qwen-baseline.md), [ADR-0004](docs/adr/0004-registered-agent-runtime-and-lifecycle-events.md), [ADR-0005](docs/adr/0005-validated-execution-state-machine.md), [ADR-0006](docs/adr/0006-default-deny-bounded-tool-runtime.md), [ADR-0007](docs/adr/0007-bounded-aged-priority-scheduler.md), [ADR-0008](docs/adr/0008-conservative-pre-scheduler-memory-admission.md), [ADR-0009](docs/adr/0009-discrete-re-admitted-inference-profiles.md), [ADR-0010](docs/adr/0010-explainable-availability-gated-model-routing.md), [ADR-0011](docs/adr/0011-sqlite-checkpoints-and-pre-invocation-recovery.md), [ADR-0012](docs/adr/0012-hash-chained-traces-and-bounded-replay.md), and [ADR-0013](docs/adr/0013-sqlite-windowed-observability-snapshots.md).

## Tests Passing

- `python -m unittest discover -s tests -v` — 117 tests passed in 19.649 seconds in the final Stage 12 gate run.
- Stage 12 focused suite — 9 tests passed for config/limit validation, exact P50/P95 aggregation, absent-value truthfulness, unified activity/failure/recovery/trace reporting, time windows, bounded drill-down, live evidence, real factory composition, and read-only machine-readable reporting.
- `python -m benchmarks.run_stage12_observability` — retained `stage12-observability-20260824T163054Z.json`; expected four-task mix and all totals matched, live hardware present, exit 0.
- Stage 12 retained live report — 1,504.908 ms collection, of which 1,498.907 ms was the live hardware profile; the same durable-only database report collected in 6.543 ms.
- Real Stage 12 agent/report — Qwen2.5 1.5B/`performance`; one task/model call/route and 18 trace steps; 2,927.102 ms inference, 2,238.325 ms TTFT, 96.16 tok/s, 1,343.703 MiB RAM, 1,189 MiB VRAM; query after restart matched every value.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.12.0`, exit 0.
- `python -m runtime --objective "Stage 12 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.

- `python -m unittest discover -s tests` — 108 tests passed in 13.895 seconds in the final Stage 11 gate run.
- Persistence plus Stage 11 focused suites — 20 tests passed; 9 specifically cover v1-to-v2 migration, structured chains, model hashes, bounded replay/no new inference, tamper detection, same/different-run comparison, tool-side-effect skipping, restart loading/factory composition, and CLI demonstration.
- `python -m benchmarks.run_stage11_trace_replay` — retained `stage11-trace-replay-20260824T143744Z.json`; two 15-step runs, replay `matched`, 10 deterministic matches, zero divergences, integrity `ok`, exit 0.
- Real Stage 11 agent — Qwen2.5 1.5B/`performance`; 2,865.074 ms total, 1,989.471 ms TTFT, 94.53 tok/s, 1,345.855 MiB RAM, 1,189 MiB VRAM; completed 18-step trace.
- Real trace inspect/replay — run `af0707f0-6133-4600-bd94-b26896879526`; 11 deterministic, 3 nondeterministic, 4 observational steps; reconstructed `completed`, 11 matches/7 observed-only, chain/SQLite integrity `ok`, exit 0.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.11.0`, exit 0.
- `python -m runtime --objective "Stage 11 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests` — 99 tests passed in 6.524 seconds in the final Stage 10 gate run.
- Stage 10 focused suite — 11 tests passed for schema version/idempotency, newer-schema rejection, illegal-transition rollback, agent conflict, durable record families, tool persistence, restart reconstruction, safe recovery, terminal/in-flight refusal, factory composition, and killed-process CLI recovery.
- `python -m runtime.recovery_cli` — worker process terminated with exit code 1 at durable `planning/recovery_ready`; restarted task completed through `recovering`; SQLite integrity `ok`, exit 0.
- `python -m benchmarks.run_stage10_recovery` — retained `stage10-recovery-20260824T131728Z.json`, final state `completed`, integrity `ok`, exit 0.
- Real Stage 10 agent — Qwen2.5 1.5B/`performance`; 2,891.000 ms task elapsed, 2,125.300 ms backend total, 1,420.839 ms TTFT, 106.76 tok/s, 1,343.590 MiB RAM, 1,189 MiB VRAM; 1 task/output, 5 transitions/checkpoints, 21 events, and 17 steps persisted.
- Real restart inspection — reconstructed task `3626f112-5c0c-4651-8eaf-68bdcddfb20a` as `completed` with `created -> planning -> executing -> validating -> completed`; integrity `ok`; model was not started.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.10.0`, exit 0.
- `python -m runtime --objective "Stage 10 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 88 tests passed in 2.898 seconds in the final Stage 9 gate run.
- Stage 9 focused suite — 9 tests passed for registry validation/availability, different workload routes, explained rejection, context overflow, token/time propagation, zero-call blocking, VRAM-budget profile fallback, factory composition, and CLI output.
- `python -m runtime.routing_cli` — live availability/routes, controlled two-model route split, seven-token cap, and zero-call rejection matched policy; exit 0.
- `python -m benchmarks.run_stage9_routing` — retained `stage9-routing-20260824T124057Z.json`; interactive explanation selected optional compact and standard risk selected installed 1.5B; exit 0.
- Real Stage 9 interactive agent — installed Qwen2.5 1.5B, `performance`, one-call/64-token budget, 32 generated runs, 2,391.000 ms task elapsed, 2,142.737 ms backend total, 1,445.427 ms TTFT, 106.54 tok/s, 1,343.715 MiB RAM, 1,189 MiB VRAM.
- Real Stage 9 background agent — installed Qwen2.5 1.5B, `balanced`, one-call/32-token budget, 25 generated runs, 5,031.000 ms task elapsed, 4,795.147 ms backend total, 1,469.083 ms TTFT, 48.83 tok/s, 1,351.633 MiB RAM, 909 MiB VRAM.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.9.0`, exit 0.
- `python -m runtime --objective "Stage 9 regression smoke task"` — deterministic stub lifecycle remained intact with zero real model calls, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

- `python -m unittest discover -s tests -v` — 79 tests passed in 2.699 seconds in the final Stage 8 gate run.
- Stage 8 focused tests — profile/catalog validation, workload ordering, one-snapshot selection, pressure fallback, missing GPU/RAM, exact native flags, applied metadata, runtime ordering/blocking, CLI, and composition passed.
- `python -m runtime.adaptive_cli` — live standard/interactive selected performance, live background selected balanced; controlled pressure/missing-GPU/missing-RAM behavior matched policy, exit 0.
- `python -m benchmarks.run_stage8_profiles --runs-per-profile 1` — two four-profile runs completed; exploratory `...T121616Z.json` exposed the zero-layer CUDA allocation and final `...T122355Z.json` verified explicit device isolation.
- Stage 8 final profile comparison — performance 100.92 tok/s and 1,189 MiB VRAM; balanced 54.97 tok/s and 909 MiB; constrained 40.41 tok/s and 527 MiB; CPU-safe 27.06 tok/s and 0 MiB.
- Stage 8 failed/kept experiment — zero GPU layers alone still used 311 MiB VRAM; explicit `--device none` reduced the repeated CPU-safe delta to 0 MiB but increased peak host RAM to 1,796.082 MiB and total time to 3,581.382 ms.
- Stage 8 estimator comparison — balanced/constrained VRAM was underpredicted by 23.774/160.110 MiB and CPU-safe host RAM by 375.172 MiB; configured 512/2,048 MiB reserves covered these observed misses, but the extrapolated estimator is not uniformly conservative.
- Stage 8 real standard agent — performance/`ACCEPT`; 2,035.135 ms total, 1,322.844 ms TTFT, 104.46 tok/s, 1,343.508 MiB RAM, 1,189 MiB VRAM, 0.1423 ms queue wait.
- Stage 8 real background agent — balanced/`ACCEPT`; 2,070.558 ms total, 1,317.198 ms TTFT, 69.04 tok/s, 1,351.746 MiB RAM, 909 MiB VRAM, 0.1215 ms queue wait.
- Stage 8 package dry run — would install `local-ai-systems-lab-0.8.0`, exit 0.
- `python -m compileall -q runtime tests benchmarks` and `git diff --check` — exit 0; line-ending notices only.
- `python -m runtime --objective "Stage 8 regression smoke task"` — deterministic stub lifecycle remained intact, exit 0.

- `pwsh -NoProfile -File .\scripts\setup_stage2.ps1` — hashes, llama.cpp version, and CUDA device verified; idempotent rerun passed.
- `python -m unittest discover -s tests -v` — 66 tests passed in 2.091 seconds in the final Stage 7 gate run.
- Stage 7 tests — actual model-file sizing, active/profile mismatch rejection, source-aware profiler parsing, unavailable RAM rejection, estimator/measured comparison, all six policy actions, pre-scheduler event order, accepted execution, and blocked backend non-invocation passed.
- `python -m runtime.hardware_cli` — live hardware/pressure report, `ACCEPT`, calibration comparison, and all six labeled controlled scenarios, exit 0.
- Stage 7 live profile — 72.267 ms; 16,618.473 MiB available RAM; 3,962 MiB free VRAM; `ACCEPT`.
- Stage 7 real admitted Qwen run — admission preceded scheduler submission; 0.2384 ms queue wait, 1,990.603 ms scheduled execution, 1,898.729 ms backend total, 1,332.861 ms TTFT, 111.59 tokens/second, 1,339.113 MiB peak RAM, and 1,219 MiB VRAM delta.
- Scheduler tests — FIFO/priority ordering, stable workload priority, starvation promotion, queued cancellation, busy-worker queue timeout, active timeout signaling, two-worker bounds, runtime result metrics, and terminal-state mapping passed.
- `python -m runtime.scheduler_cli` — same queued submission order produced the expected distinct FIFO and priority execution orders, exit 0.
- Stage 6 controlled priority run — peak queue depth 3; queue-wait P50 0.1344 ms and P95 0.6520 ms.
- Stage 6 controlled FIFO run — queue-wait P50 0.3727 ms and P95 0.7256 ms.
- Stage 6 real scheduled Qwen run — completed with 0.1786 ms queue wait and 1,988.50 ms scheduled execution boundary.
- Stage 6 real inference — 1,898.38 ms backend total, 1,324.55 ms TTFT, 113.77 tokens/second, 1,339.23 MiB peak RAM, and 1,219 MiB VRAM delta.
- Tool tests — permitted result/history, exact-grant denial, path escape, strict types, registry duplicate/missing, timeout signal, external cancellation, invalid result, and cancelled terminal state passed.
- `python -m runtime.tool_cli --demo` — permitted request completed, expected unauthorized request returned `tool_permission_denied`, and command exited 0.
- Stage 5 permitted read — 2.9874 ms tool-handler boundary; `created -> planning -> waiting_for_tool -> validating -> completed`; no inference call.
- Stage 5 denied read — `created -> planning -> security_blocked`; handler was not invoked.
- State-machine tests — deterministic success, illegal jump details, every failure terminal, terminal non-reentry, tool-wait return path, and typed runtime failure mapping passed.
- Native failure-classification test — OOM, context overflow, and generic llama.cpp failures map to distinct typed errors.
- `python -m runtime.agent_cli --agent technical-explainer` — real Qwen execution exposed `created -> planning -> executing -> validating -> completed` with ordered reasons/timestamps.
- Stage 4 real run — 1,825.54 ms total, 1,281.54 ms TTFT, 113.37 tokens/second, 1,339.04 MiB peak RAM, 1,219 MiB VRAM delta.
- `python -m benchmarks.run_stage2_baseline --runs-per-prompt 1` — retained five-run real inference baseline passed.
- Real `--cancel-after-ms 1800` verification — structured cancellation, exit code 130, and GPU memory release passed during Stage 2.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.6.0`, exit 0.
- Stage 7 package dry run — would install `local-ai-systems-lab-0.7.0`, exit 0.
- `python -m runtime --objective "Stage 4 regression smoke task"` — four-event deterministic stub lifecycle remained intact, exit 0.
- `python -m runtime --objective "Stage 7 regression smoke task"` — deterministic stub lifecycle remained intact, exit 0.
- `git diff --check` — exit 0; line-ending notices only.

## Known Problems

- Automatic recovery resumes only from a pre-invocation planning checkpoint; native token generation and arbitrary tool/model execution cannot be resumed.
- Scheduler queue/worker internals are not reconstructed; a safe recovered task is resubmitted through current policy, routing, admission, and scheduling.
- A second crash after entering `RECOVERING` is classified unsafe rather than automatically retried.
- Terminal state and output are committed in adjacent transactions; a narrow crash window can leave a terminal task without output, which requires manual repair rather than unsafe duplication.
- SQLite is local single-host persistence, not distributed coordination or a multi-process cluster database.
- Database backup/restore, compaction/retention, encryption at rest, and forward migration beyond schema v2 are not implemented.
- Trace hashes provide tamper evidence but are not signed/authenticated against an attacker able to rewrite both payloads and hashes.
- Trace payloads can retain local objectives, tool arguments, and outputs; redaction/export/retention policy is not implemented.
- Replay reconstructs deterministic execution evidence; it does not rerun llama.cpp token generation, reproduce hardware timing, or repeat tool side effects.
- Pre-Stage-11 data migrates safely but is not backfilled into fabricated historical trace runs.
- Cross-run comparison is structural/semantic hash comparison, not model-output quality evaluation.

- Only one real GGUF/backend is installed and configured; real multi-model switching is not claimed.
- The compact registry entry is unavailable and unbenchmarked; its controlled route uses simulated availability with the stub-compatible boundary only.
- Capability labels and quality ranks are static policy metadata; output validation still cannot prove semantic correctness.
- Budget memory enforcement uses preflight estimates; observed peak measurements are reported afterward and estimator misses remain possible.
- The router and adaptive controller take separate live hardware snapshots, so pressure can change between model selection and exact profile admission; the later admission decision remains authoritative.
- Routing decisions, budgets, and usage records now appear in the Stage 12 unified task/report view; semantic output evaluation remains future work.

- Queue state and request handles remain process-local; durable lifecycle/metric events survive, but the scheduler queue itself is not reconstructed.
- The public `AgentRuntime.run()` call waits synchronously even though scheduler requests are internally queued.
- Python cannot forcibly stop a non-cooperative scheduled operation thread; logical timeout/cancellation returns and signals the token.
- Priority defaults and aging/starvation thresholds are transparent baselines, not workload-tuned optimal values.
- Adaptation is limited to four discrete profiles; continuous recommendation-to-parameter conversion is intentionally absent.
- The scheduler does not preempt an operation that has already started.
- Tool timeout returns control and signals cancellation, but Python cannot forcibly stop a non-cooperative handler thread; only vetted handlers are permitted.
- The two safe tools provide application-level path containment, not process or OS sandboxing.
- Tool definitions and grants remain static in code; tool invocation requests/results/errors are durable.
- Only read-only project text tools exist; writes, subprocesses, network access, and arbitrary binary reads remain prohibited.
- Output validation only rejects blank text and does not detect semantic role/factual failures.
- Transition histories, agent snapshots, lifecycle events, metrics, checkpoints, traces, and replay reports are durable in SQLite schema v2.
- An intermediate real prompt experiment completed but inverted privacy wording and drifted into training; bounded role prompts corrected the final run, but no output validator exists.
- The real backend reloads the model for every request, making median cold TTFT about 1.69 seconds.
- The backend accepts only one active inference per instance; the real scheduler is deliberately configured with one worker.
- VRAM is sampled at 200 ms via total-device `nvidia-smi` data and can include unrelated GPU use.
- The five-prompt, single-iteration sample is acceptance evidence, not a statistically strong performance claim.
- A 64-token cap truncated some longer answers; one JSON-only prompt included Markdown fences, so no broad quality claim is made.
- Routing is static and the identity policy is not a security sandbox.
- Observability is pull-based and local; there is no remote collector, alerting pipeline, public API, or frontend.
- Live scheduler state belongs to the reporting runtime process; historical scheduler behavior is represented separately by durable event distributions.
- Recent task drill-down uses bounded follow-up queries and is not yet optimized for large databases.
- Physical core count is not accessible through the narrow live profiler and remains explicitly unavailable; the declared eight-core constraint is not relabeled as observed.
- The memory estimator is calibrated against one model/configuration/run. It does not establish accuracy for larger models, quantizations, contexts, or concurrency.
- `nvidia-smi` reports device-wide pressure and can include unrelated GPU allocations.
- `QUEUE` is an advisory admission decision and does not silently enter the execution scheduler; callers must retry so memory is re-profiled.
- Profile measurements contain one run per profile and cannot support strong statistical or universal tuning claims.
- Balanced/constrained profiles change several variables together, so this experiment cannot isolate which flag caused a difference.
- Zero GPU layers alone still initialized 311 MiB VRAM; CPU-safe now also requires `--device none`, which measured 0 MiB but increases host RAM/latency.
- Profile catalog values and workload order are static, model-specific, and not learned from benchmark history.
- The Stage 7 estimator underpredicts some Stage 8 profiles; reserves covered the observed sample, but per-profile recalibration remains necessary.
- No Python dependency lock is necessary while project dependencies remain empty; revisit this when a Python dependency is introduced.
- WMI/CIM hardware queries are access-restricted in the current execution context; the environment checker uses narrower registry/.NET/NVIDIA queries.
- The Windows registry product label reports `Windows 10 Home Single Language` while build/display-version evidence is `26200.9168` / `25H2`; the report preserves the raw evidence rather than inferring a marketing name.
- The installed Hugging Face CLI 0.36.0 lacks newer `hf models info`/dry-run forms; exact Hub revision metadata and the pinned download path were used instead.
- The first benchmark file-path invocation failed to import `runtime`; the benchmark became a package and the documented module invocation passed.

## Performance Baseline

The Stage 2 five-run cold baseline remains: median model load 1,128.28 ms; TTFT 1,686.85 ms; generation 115.81 tokens/second; total 2,572.26 ms; peak child-process RAM 1,339.02 MiB; VRAM delta 1,219 MiB. The final Stage 8 comparison observed performance/balanced/constrained/CPU-safe VRAM deltas of 1,189/909/527/0 MiB. Stage 12 real inference measured 2,927.102 ms total, 2,238.325 ms TTFT, 96.16 tokens/second, 1,343.703 MiB RAM, and 1,189 MiB VRAM; the post-restart report recovered all measurements and the 18-step trace identity. The retained controlled report collected durable plus live telemetry in 1,504.908 ms, dominated by its 1,498.907 ms hardware profile; durable-only collection was 6.543 ms. See [the Stage 2 report](docs/benchmarks/stage2-local-inference-baseline.md), [Stage 8 final comparison](benchmarks/results/stage8-profile-comparison-20260824T122355Z.json), [Stage 12 result](benchmarks/results/stage12-observability-20260824T163054Z.json), and [Stage 12 report](docs/stages/stage12-observability-metrics-backend.md).

## Backend Acceptance Status

NOT STARTED. The Backend Acceptance Gate is Stage 16.

## Frontend Research Status

NOT STARTED. Production frontend work remains prohibited until backend acceptance. Stage 17 research is also not current-stage work.

## Next Step

Stage 13 — Fault Injection / Chaos Framework

## Later Backlog

Stages 13–27 remain intentionally deferred and must be entered one at a time after explicit approval.
