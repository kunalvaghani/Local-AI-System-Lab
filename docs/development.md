# Development and Verification Commands

## Current setup

The Python package supports Python 3.10 or newer and has no third-party runtime
or test dependencies. Stage 2 additionally uses pinned, ignored native binaries
and a GGUF model. `pyproject.toml` and `configs/inference-baseline.json` are the
tracked package/inference sources of truth.

Clone and inspect:

```powershell
git clone https://github.com/kunalvaghani/Local-AI-System-Lab.git
Set-Location Local-AI-System-Lab
git status --short --branch
```

Collect the environment baseline:

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

Run the lifecycle demonstration:

```powershell
python -m runtime --objective "Demonstrate one local task"
```

Install or verify the pinned Stage 2 artifacts (network is used only when an
artifact is absent):

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
```

Run real local inference:

```powershell
python -m runtime.inference_cli --prompt "Explain local inference in one sentence." --json
```

Run both specialized agents through the current validated runtime:

```powershell
python -m runtime.agent_cli
```

Run the Stage 5 permitted/denied tool demonstration (no model load):

```powershell
python -m runtime.tool_cli --demo
```

Compare FIFO and priority scheduling with the same controlled queued workload:

```powershell
python -m runtime.scheduler_cli
```

The JSON output includes submission/execution order, per-request queue and
execution latency, queue depth, completion counts, and P50/P95/max queue wait.

Inspect live hardware, the conservative model estimate, calibration error, the
current admission decision, and controlled coverage of all decision branches:

```powershell
python -m runtime.hardware_cli
```

Only the live snapshot is hardware evidence. The six-branch policy examples in
the same report are labeled controlled synthetic scenarios.

Inspect Stage 8 profile definitions and selection without launching inference:

```powershell
python -m runtime.adaptive_cli
```

Execute the same real workload through every tracked profile and write a
timestamped comparison under `benchmarks/results/`:

```powershell
python -m benchmarks.run_stage8_profiles --runs-per-profile 1
```

Select a workload class for a real agent execution:

```powershell
python -m runtime.agent_cli --agent technical-explainer --workload background
```

Inspect Stage 9 registry availability, route explanations, and budget controls:

```powershell
python -m runtime.routing_cli
python -m benchmarks.run_stage9_routing
```

Exercise Stage 10 process interruption and restart recovery:

```powershell
python -m runtime.recovery_cli
python -m benchmarks.run_stage10_recovery
```

Inspect, replay, and compare Stage 11 traces without invoking a real model:

```powershell
python -m runtime.trace_cli demo
python -m benchmarks.run_stage11_trace_replay
```

Inspect/replay a specific durable run:

```powershell
python -m runtime.trace_cli inspect --database data/runtime-stage11.db --task-id TASK_ID
python -m runtime.trace_cli replay --database data/runtime-stage11.db --run-id RUN_ID
python -m runtime.trace_cli compare --database data/runtime-stage11.db --left-run-id LEFT --right-run-id RIGHT
```

Run real inference against an explicit ignored SQLite database:

```powershell
python -m runtime.agent_cli --agent technical-explainer --database data/stage11-local.db
```

The result includes `route`, `compute_budget`, `compute_usage`,
`profile_selection`, the final admission decision, the exact applied
`inference_profile`, scheduler evidence, and inference metrics.

Run a single typed read-only tool request:

```powershell
python -m runtime.tool_cli --agent technical-explainer --tool project_context_read --arguments '{"relative_path":"docs/architecture.md","max_characters":1000}'
```

Inspect one real task's ordered state history:

```powershell
python -m runtime.agent_cli --agent technical-explainer
```

Run one registered role with an objective override:

```powershell
python -m runtime.agent_cli --agent risk-analyst --objective "State one local-inference memory risk and mitigation."
```

Exercise owned-process cancellation:

```powershell
python -m runtime.inference_cli --prompt "Write a long explanation." --max-tokens 64 --cancel-after-ms 1800
```

Run and record a new five-prompt cold baseline:

```powershell
python -m benchmarks.run_stage2_baseline --runs-per-prompt 1
```

Run the standard-library test suite:

```powershell
python -m unittest discover -s tests -v
```

Validate Python syntax without executing application code:

```powershell
python -m compileall -q runtime tests benchmarks
```

Validate package metadata without installing the project or dependencies:

```powershell
python -m pip install --dry-run --no-deps --no-build-isolation .
```

Inspect tracked project files without descending into `.git`:

```powershell
rg --files -uu -g '!.git/**'
```

Check unfinished-work markers:

```powershell
rg -n -uu -g '!.git/**' 'TODO|FIXME|HACK|XXX' .
```

Review local changes:

```powershell
git status --short
git diff --check
git diff
```

## Commands intentionally undefined

SQLite schema migration is applied automatically on store open. There is no API
server or frontend command because those capabilities do not exist yet. Formatting,
linting, type-checking, and coverage tools are not declared until their cost and
configuration are selected in a later approved stage.

## Development discipline

1. Read `PROJECT_STATE.md` and the relevant architecture/ADR documents.
2. Confirm the explicitly approved stage and its stopping point.
3. Inspect status, source, tests, configs, and TODO markers before editing.
4. Make the smallest implementation that produces the stage's new capability.
5. Run real tests and record exact commands/results.
6. Update `PROJECT_STATE.md` to evidence, then stop for approval.

Performance work follows:

```text
BASELINE -> PROFILE -> HYPOTHESIS -> CHANGE -> BENCHMARK -> KEEP/REVERT
```
