# Current Project State

## Active Project

Local AI Systems Lab — a fully local, inspectable AI runtime/platform for constrained consumer hardware.

## Current Milestone

Runnable component skeleton established; waiting at the Stage 1 approval gate.

## Current Stage

Stage 1 — Project Skeleton & Core Interfaces — COMPLETE, AWAITING APPROVAL.

## Current Subsystem

Typed runtime contracts, synchronous lifecycle orchestration, deterministic in-memory adapters, and developer CLI.

## Last Completed Work

- Added Python 3.10-compatible package metadata with zero runtime dependencies.
- Added typed Agent, Task, inference, routing, policy, checkpoint, metrics, result, and configuration data.
- Added structured serializable runtime/configuration/validation/component errors.
- Added replaceable protocols for inference, scheduling, routing, policy, checkpoints, and metrics.
- Implemented `AgentRuntime` start, task creation/execution, and idempotent shutdown composition.
- Added deterministic stub inference, inline scheduling, static routing, identity policy, and process-local checkpoint/metric stores.
- Added a JSON CLI demonstration explicitly reporting zero real LLM calls.
- Added 13 standard-library unit/integration tests covering lifecycle, protocols, errors, denial, component failure, and CLI output.
- Added ADR-0002 and updated architecture, development, repository, and risk evidence.

## Currently Working On

None. Stage 1 is complete and work is stopped at the mandatory approval gate.

## Current Blockers

- User approval is required before Stage 2.
- `llama-cli` is not installed or not on `PATH`; Stage 2 must choose and reproduce the local inference installation path.
- No GGUF model has been selected or downloaded; this is intentionally deferred to Stage 2.

## Important Decisions

- Follow one stage at a time and stop for explicit approval after each stage.
- Complete and accept the backend before production frontend work.
- Keep important runtime logic framework-independent and inspectable.
- Use Python as the initial implementation language; require measured evidence before introducing C++.
- Treat observed repository state and executed tests as higher-confidence evidence than plans.
- Use Python structural protocols and constructor injection for current component boundaries.
- Keep Stage 1 synchronous and dependency-free until real inference/scheduling requirements provide evidence for async or third-party tooling.

See [ADR-0001](docs/adr/0001-stage-gated-modular-backend-first.md) and [ADR-0002](docs/adr/0002-typed-protocols-and-stdlib-skeleton.md).

## Tests Passing

- `pwsh -NoProfile -File .\scripts\check_environment.ps1` — exit 0.
- `python -m unittest discover -s tests -v` / `-q` — 13 tests passed in three runs (0.195–0.254 seconds), exit 0.
- `python -m runtime --objective "Stage 1 smoke task"` — complete four-event lifecycle, exit 0.
- `python -m compileall -q runtime tests` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — metadata prepared; would install `local-ai-systems-lab-0.1.0`, exit 0.
- Local Markdown link verification — all local links resolved, exit 0.
- Required `PROJECT_STATE.md` heading verification — all 15 headings present, exit 0.
- Deferred-dependency scope audit and source-marker audit — clean, exit 0.
- `git diff --check` — exit 0 (Git emitted only its Windows LF-to-CRLF working-copy warning).

## Known Problems

- Inference is deterministic stub text only; no model is loaded and no real tokens are generated.
- The scheduler executes immediately on the caller thread; it has no queue, priority, timeout, cancellation, starvation, or concurrency behavior.
- Routing is static and the identity policy is not a security sandbox.
- Checkpoints and metric events are process-local, non-durable, and make no thread-safety guarantee.
- Streaming, cancellation, token metrics, hardware profiling, admission control, tools, persistence, replay, API, and frontend do not exist.
- No dependency lock is necessary while project dependencies remain empty; this must be revisited when Stage 2 adds dependencies/tools.
- WMI/CIM hardware queries are access-restricted in the current execution context; the environment checker uses narrower registry/.NET/NVIDIA queries.
- The Windows registry product label reports `Windows 10 Home Single Language` while build/display-version evidence is `26200.9168` / `25H2`; the report preserves the raw evidence rather than inferring a marketing name.
- Ollama client 0.32.14 is installed, but no running Ollama service was reachable during inspection.
- A Python 3.10-only auxiliary metadata check using `tomllib` failed because `tomllib` enters the standard library in Python 3.11; package validation then passed using pip on Python 3.10 and `tomllib` on Python 3.11.

## Performance Baseline

The 13-test Stage 1 suite completed in 0.195–0.254 seconds across three runs. This is not an inference benchmark. TTFT, tokens/second, prompt processing, model load time, RAM delta, and VRAM delta remain `UNKNOWN` because no real inference backend or model has been integrated.

## Backend Acceptance Status

NOT STARTED. The Backend Acceptance Gate is Stage 16.

## Frontend Research Status

NOT STARTED. Production frontend work remains prohibited until backend acceptance. Stage 17 research is also not current-stage work.

## Next Step

Stage 2 — Local Inference Baseline

## Later Backlog

Stages 3–27 remain intentionally deferred and must be entered one at a time after explicit approval.
