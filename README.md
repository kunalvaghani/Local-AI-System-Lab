# Local AI Systems Lab

A stage-gated portfolio project for building an inspectable local AI runtime on
constrained consumer hardware. Specialized agents now have an inspectable,
transition-validated runtime, bounded scheduling, memory admission, adaptive profiles,
explainable model routing, task-scoped compute budgets, durable recovery, and
hash-chained execution traces with bounded replay. Stage 12 adds unified live
and recent runtime telemetry, Stage 13 adds explicitly armed fault experiments,
and Stage 14 adds deterministic security boundaries plus repeatable adversarial
PASS/FAIL evidence. Stage 15 exposes the complete runtime through a documented,
loopback-only HTTP/JSON and SSE backend API. Stage 16 verifies the entire backend
through a reproducible acceptance gate with scoped maturity classifications.
Stage 17 completes fresh frontend research and Stage 18 turns its Systems
Cartography direction into a measured, navigable local React application shell
and reusable design system without fabricating backend telemetry. Stage 19 adds
the real local Runtime Command Center: live inspection, bounded task launch,
URL-addressable task evidence, ordered SSE lifecycle updates, and cancellation.

## Current status

- Last completed stage: Stage 19 — Runtime Command Center
- Next approval-gated stage: Stage 20 — Scheduler & Task Graph
- Backend acceptance: RELEASE CANDIDATE; all required checks PASS, overall maturity PARTIAL
- Frontend Runtime Command Center: COMPLETE; specialist screens remain staged

See [PROJECT_STATE.md](PROJECT_STATE.md) for the source-of-truth status.

## Run the Stage 19 Runtime Command Center

Start the local-only deterministic API from the repository root:

```powershell
python -m runtime.api_cli --stub --database data/stage19-dev.db
```

In a second terminal:

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:4173/runtime`. The command center reads real health,
scheduler, hardware, model, agent, and metric evidence through the loopback
proxy. It can launch one bounded task, retain its selected ID in the URL, follow
ordered SSE lifecycle events, show truthful output/measurements, and request
cooperative cancellation. It does not fabricate a task history the API lacks.

Validate the frontend foundation:

```powershell
npm test
npm run build
npm run check:bundle
npm run smoke:stage19
```

The Stage 19 suite has seven component tests including an automated axe-core
scan. Its reproducible smoke crosses the Vite proxy, creates a real stub task,
reads 15 ordered lifecycle events, and retains JSON evidence. Read the
[Stage 19 report](docs/stages/stage19-runtime-command-center.md) and
[ADR-0019](docs/adr/0019-real-loopback-query-and-sse-client.md).

## Review the Stage 17 frontend research

Read [the frontend research and recommendation](docs/frontend-research.md) for
28 current references covering official Google work, recent browser capabilities,
developer and observability interfaces, and maintained React implementation
candidates. It recommends a custom Systems Cartography direction, a lean
accessible/virtualized stack, explicit performance and accessibility constraints,
and a list of rejected or deferred ideas.

The research is retained as the decision evidence behind the Stage 18 shell and
Stage 19 Runtime Command Center.

## Run the Stage 16 backend acceptance gate

Execute the complete build/package, test, control, scheduler, hardware, recovery,
trace, observability, chaos, security, deterministic API, and real-model API gate:

```powershell
python -m benchmarks.run_stage16_acceptance
```

The retained run executed 14 commands, passed all 14 mandatory categories, ran
150 tests, completed one real Qwen/llama.cpp API task, and passed five regression
limits. The backend is a release candidate for single-user loopback frontend
work, but overall maturity remains `PARTIAL`: the terminal-output atomicity gap,
one-real-model/semantic-evaluation boundary, and application-level security limit
remain explicit. See the [Backend Acceptance Report](docs/backend-acceptance-report.md)
and [Stage 16 report](docs/stages/stage16-backend-verification-acceptance-gate.md).

## Operate the Stage 15 backend API

Start the deterministic full-runtime composition with zero real LLM calls:

```powershell
python -m runtime.api_cli --stub
```

Start the real guarded Qwen/llama.cpp composition:

```powershell
python -m runtime.api_cli
```

The loopback base URL is `http://127.0.0.1:8765/v1`; its OpenAPI document is at
`/v1/openapi.json`. The contract creates/inspects/cancels tasks, streams lifecycle
events over SSE, and inspects agents, scheduler, hardware, models, metrics,
redacted traces/replay, isolated chaos results, and retained security evidence.
It serves no static files and is not an internet-facing production server.

Run the separate-process external evidence workflow:

```powershell
python -m benchmarks.run_stage15_api
```

The retained deterministic run completed 16 HTTP/SSE operations with zero direct
runtime calls after launch and zero real LLM calls. A second retained real run
completed the same 16-operation workflow through Qwen2.5 1.5B/llama.cpp with one
real model call, valid trace replay, expected isolated chaos, zero retained
security failures, and SQLite integrity `ok`. See the
[Stage 15 report](docs/stages/stage15-backend-api-full-runtime-integration.md).

## Run Stage 14 adversarial tests

Run all 14 bounded cases or select individual cases:

```powershell
python -m runtime.security_cli
python -m runtime.security_cli --case prompt-injection --case tool-escalation
python -m benchmarks.run_stage14_security
```

The suite exercises input/output validation, prompt authority separation, path
allowlists, tool and network ceilings, secret redaction, subprocess rules,
timeouts, process limits, malformed structures, and resource abuse. Its retained
run passed 14/14 cases with zero real LLM calls and SQLite integrity `ok`.
Passing these tests does not prove the system is secure. See the
[Stage 14 report](docs/stages/stage14-security-adversarial-testing.md).

## Run Stage 13 chaos experiments

Fault injection is disabled by default. Explicitly arm one deterministic
scenario or the complete controlled suite:

```powershell
python -m runtime.chaos_cli --execute --scenario model-timeout
python -m runtime.chaos_cli --execute
python -m benchmarks.run_stage13_chaos
```

The report includes expected/actual state and error, injection evidence, traces,
latency relative to no-fault baselines, containment, task completion, recovery,
observability, and SQLite integrity. The retained suite matched 9/9 expected
outcomes and recovered its killed worker, while truthfully reporting the known
terminal-output database gap as not contained. See the
[Stage 13 report](docs/stages/stage13-fault-injection-chaos-framework.md).

## Inspect Stage 12 observability

Create controlled inference, tool, denied-operation, and recovery activity, then
emit one JSON report with task states, activity totals, latency/resource
distributions, live scheduler state, source-labelled hardware, and per-task drill-down:

```powershell
python -m runtime.observability_cli demo
python -m benchmarks.run_stage12_observability
```

Query an existing local database without invoking a real model:

```powershell
python -m runtime.observability_cli report --database data/runtime-stage12.db
```

Missing measurements remain `null` with a zero sample count. Recovery attempts
are reported as retries because no separate generic retry subsystem exists. See
the [Stage 12 report](docs/stages/stage12-observability-metrics-backend.md).

## Inspect Stage 11 traces and replay

Run two equivalent deterministic-stub tasks, load their persisted traces,
integrity-check and replay the first, then compare both runs:

```powershell
python -m runtime.trace_cli demo
python -m benchmarks.run_stage11_trace_replay
```

Inspect or replay an existing trace without repeating model/tool effects:

```powershell
python -m runtime.trace_cli inspect --database data/runtime-stage11.db --task-id TASK_ID
python -m runtime.trace_cli replay --database data/runtime-stage11.db --run-id RUN_ID
```

Trace records include run/step identity, actor/component, UTC timestamp,
canonical input/output hashes, a hash chain, state/model/configuration/failure
metadata, and an explicit determinism class. See the
[Stage 11 report](docs/stages/stage11-execution-trace-deterministic-replay.md).

## Inspect Stage 10 persistence and recovery

Launch a checkpointed worker, terminate its process, restart against the same
SQLite database, and recover the original task:

```powershell
python -m runtime.recovery_cli
```

Retain a compact recovery result:

```powershell
python -m benchmarks.run_stage10_recovery
```

Real agent execution now uses the ignored `data/runtime-stage15.db` database by
default. Use `--database` to select another local database. See the
[Stage 10 purpose, component map, recovery contract, and evidence](docs/stages/stage10-persistence-checkpoints-recovery.md).

## Inspect Stage 9 routing and budgets

Show truthful live model availability, explained routes, controlled two-model
route differences, token capping, and a zero-call budget rejection:

```powershell
python -m runtime.routing_cli
```

Retain the controlled routing comparison:

```powershell
python -m benchmarks.run_stage9_routing
```

Real agent results now include `route`, `compute_budget`, `compute_usage`, exact
profile/admission evidence, scheduler measurements, and inference metrics. See
the [Stage 9 purpose, component map, evidence, and limits](docs/stages/stage9-model-registry-router-budgets.md).

## Inspect Stage 8 adaptive inference

Show the four explicit profiles, live workload selections, and controlled
pressure/missing-telemetry behavior without loading the model:

```powershell
python -m runtime.adaptive_cli
```

Run a real standard or background agent so the selected profile is applied to
llama.cpp and returned with its measurements:

```powershell
python -m runtime.agent_cli --agent technical-explainer --workload standard
python -m runtime.agent_cli --agent technical-explainer --workload background
```

Run the same real prompt through every profile:

```powershell
python -m benchmarks.run_stage8_profiles --runs-per-profile 1
```

See the [Stage 8 purpose, component map, and measured comparison](docs/stages/stage8-adaptive-inference-controller.md).

## Inspect Stage 7 hardware and admission

Capture current resource evidence, inspect the baseline estimate and measured
error, and exercise all six controlled admission outcomes:

```powershell
python -m runtime.hardware_cli
```

The live result is evaluated before Stage 6 scheduler submission. Only `ACCEPT`
executes; other decisions carry a recommendation and enter `RESOURCE_BLOCKED`.
See the [Stage 7 purpose and component upgrade map](docs/stages/stage7-hardware-profiler-admission.md).

## Run the Stage 6 scheduler comparison

Submit the same background, standard, and interactive workload under FIFO and
priority policies, then inspect execution order and queue metrics:

```powershell
python -m runtime.scheduler_cli
```

The FIFO path preserves submission order. The priority path executes interactive
work first, while aging and a maximum-wait promotion protect old background work.
See the [Stage 6 purpose and component upgrade map](docs/stages/stage6-request-scheduler.md).

## Run the Stage 5 tool runtime

Run one permitted read-only request and one expected denied request without
loading the model:

```powershell
python -m runtime.tool_cli --demo
```

Run one explicit typed request:

```powershell
python -m runtime.tool_cli --agent technical-explainer --tool project_context_read --arguments '{"relative_path":"README.md","max_characters":600}'
```

The safe tools can read only approved UTF-8 text below the resolved project
root. Exact per-agent grants and required permission names are checked before
execution. See the [Stage 5 purpose and component upgrade map](docs/stages/stage5-tool-runtime-permissions.md).

## Run the real agent runtime

Python 3.10 or newer, PowerShell 7, the Hugging Face CLI, and a compatible
NVIDIA GPU/driver are required for the pinned Windows CUDA baseline. Install
and verify the ignored native/model artifacts:

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
```

Run both specialized agents through task creation, validated state transitions,
policy, routing, adaptive profile selection, profile-specific admission, the bounded priority scheduler, real model invocation,
validation, and lifecycle events:

```powershell
python -m runtime.agent_cli
```

Run one agent with an overridden objective:

```powershell
python -m runtime.agent_cli --agent technical-explainer --objective "Explain GGUF in 30 words."
```

Each result includes `state_history`, normally:

```text
created -> planning -> executing -> validating -> completed
```

See the [Stage 4 state-machine report](docs/stages/stage4-explicit-state-machine.md).

## Run direct local inference

Generate locally and print the result plus measurements as JSON:

```powershell
python -m runtime.inference_cli --prompt "Explain why local inference can improve privacy." --json
```

Run the tracked five-prompt baseline:

```powershell
python -m benchmarks.run_stage2_baseline --runs-per-prompt 1
```

The setup is pinned to llama.cpp `b10566` and the Q4_K_M file from
the Apache-2.0-licensed `Qwen/Qwen2.5-1.5B-Instruct-GGUF`; exact revisions and SHA-256 values live in
[`configs/inference-baseline.json`](configs/inference-baseline.json).

## Run the deterministic lifecycle

Python 3.10 or newer is required. The skeleton has no third-party runtime
dependencies.

```powershell
python -m runtime --objective "Demonstrate one local task"
```

The command prints JSON lifecycle events for:

```text
runtime.started -> task.created -> task.completed -> runtime.stopped
```

This regression path remains clearly marked `STUB (no LLM inference)` and
reports zero real LLM calls.

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

## Engineering documentation

- [Repository map](docs/repository-map.md)
- [Architecture baseline](docs/architecture.md)
- [Frontend research](docs/frontend-research.md)
- [Frontend design system and UI architecture](docs/frontend-design-system.md)
- [Environment report](docs/environment.md)
- [Development commands](docs/development.md)
- [Risk register](docs/risks.md)
- [Stage 2 benchmark report](docs/benchmarks/stage2-local-inference-baseline.md)
- [Architecture decisions](docs/adr/README.md)

## Verify this machine

From PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

The script is read-only. It reports relevant local hardware and tool versions;
it does not install dependencies, start services, or download models.
