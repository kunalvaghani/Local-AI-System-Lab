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

Generate and retain the controlled Stage 12 observability report:

```powershell
python -m runtime.observability_cli demo
python -m benchmarks.run_stage12_observability
```

Query durable recent telemetry, optionally excluding live probes:

```powershell
python -m runtime.observability_cli report --database data/runtime-stage12.db
python -m runtime.observability_cli report --database data/runtime-stage12.db --window-minutes 15 --limit 20 --event-limit 50 --no-live
```

Run explicitly armed Stage 13 fault experiments. Omitting `--execute` is a
structured refusal and leaves the runtime inert:

```powershell
python -m runtime.chaos_cli --execute --scenario model-timeout
python -m runtime.chaos_cli --execute
python -m benchmarks.run_stage13_chaos
```

Run real inference against an explicit ignored SQLite database:

```powershell
python -m runtime.agent_cli --agent technical-explainer --database data/stage13-local.db
```

Run the complete Stage 14 adversarial suite, selected cases, or retain its
machine-readable evidence:

```powershell
python -m runtime.security_cli
python -m runtime.security_cli --case prompt-injection --case network-exfiltration
python -m benchmarks.run_stage14_security
```

The suite performs no real LLM calls or real network/shell exfiltration. It
tests deterministic policy boundaries and must not be presented as proof that
the complete system is secure.

Run the guarded real Stage 14 composition:

```powershell
python -m runtime.agent_cli --agent technical-explainer --database data/stage14-local.db
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

Start the Stage 15 loopback API with deterministic inference:

```powershell
python -m runtime.api_cli --stub
```

Use `python -m runtime.api_cli` for the real pinned local model. Both commands
bind to the tracked literal loopback address and expose the contract at
`/v1/openapi.json`. Override an ignored database with `--database`; use `--port 0`
for an ephemeral test port.

Run the external-process API evidence workflow:

```powershell
python -m benchmarks.run_stage15_api
```

The runner launches a child API process and performs task, SSE, inspection,
replay, chaos, security-result, and health operations strictly over HTTP.

Run the complete Stage 16 backend acceptance gate:

```powershell
python -m benchmarks.run_stage16_acceptance
```

The versioned policy in `configs/acceptance.json` requires 150 tests, all nine
chaos outcomes, all fourteen security cases, successful killed-process recovery,
both deterministic and real-model API workflows, and fixed real-inference
regression bounds. The command returns nonzero if a mandatory category fails and
retains a compact hashed JSON result under `benchmarks/results/`.

## Stage 25 local Runtime Workbench

### One-command Windows setup and launch

From the repository root, run:

```powershell
.\setup_and_run.bat
```

The launcher verifies Python/Node/npm, prepares missing pinned llama.cpp and
Qwen GGUF artifacts through `scripts/setup_stage2.ps1`, installs exact lockfile
dependencies with `npm ci` when needed, starts the loopback backend, waits for
`/v1/health`, verifies the Stage 27 `/v1/tools` contract, then starts Vite and
opens `/runtime`. Existing services are reused only when the requested backend
mode/contract and the frontend Stage 27/0.27.0 release marker match. The launcher
refuses to kill an unknown, stale, or mode-mismatched port owner.
An existing dependency tree is reused only after `npm ls --depth=0` succeeds.
`--install` refuses to run while port 4173 is active because Windows can keep
Vite/Rolldown native dependencies locked; stop that frontend before requesting
the clean `npm ci` reinstall.

The real local model is the default. Development and optional-service examples:

```powershell
.\setup_and_run.bat --stub
.\setup_and_run.bat --with-ollama
.\setup_and_run.bat --stub --no-browser --skip-setup
```

`--with-ollama` starts Ollama only when explicitly requested. Ollama remains a
separate convenience service; the Runtime API continues to use the pinned
llama.cpp executable and Qwen GGUF so its measured path is unchanged. Use
`setup_and_run.bat --help` for every option.

The browser shell is local-only and requires Node.js compatible with Vite 8.
Install its locked dependencies once:

```powershell
cd apps/web
npm ci
```

Start the deterministic loopback API from the repository root:

```powershell
python -m runtime.api_cli --stub --database data/stage25-dev.db
```

Start the loopback development server from `apps/web` in a second terminal:

```powershell
npm run dev
```

Open `http://127.0.0.1:4173/runtime`, `/agents`, `/scheduler`,
`/traces?task=<task-id>`, `/hardware`, `/metrics`, `/chaos`, or `/security`. The development
server proxies only `/v1` to `http://127.0.0.1:8765`. A validated `?task=`
selection is preserved between these routes so agent state, admission,
scheduler placement, timing, trace steps, replay outcomes, and cancellation
describe the same execution. A validated optional `?step=` makes one expanded
trace record refreshable without moving runtime evidence into browser storage.

Run component, navigation, preference, no-fake-data, and automated accessibility
checks, then compile and measure the shell:

```powershell
npm test
npm run build
npm run check:bundle
npm run smoke:stage25
```

The bundle script reads built JavaScript, compresses it with gzip, and fails
above 250 KiB. The Stage 25 smoke assumes both local services are running,
requests all twelve workbench routes, calculates tracked dark-theme contrast
pairs from source tokens, checks reflow/reduced-motion and stream-batching/bound
contracts, crosses the frontend proxy for health, and verifies the unchanged
running runtime and persistence integrity. The component suite owns keyboard,
focus return, skip navigation, reduced motion, slow responses, 500-event stream
bursts, 10,000-step trace bounds, and automated accessibility evidence. The
retained Stage 25 report adds a five-viewport Chromium matrix and accessibility-
tree inspection. Timestamped JSON is written under
`benchmarks/results/`. `dist/`, `node_modules/`, coverage, and
browser-test outputs stay ignored.

## Stage 26 product acceptance

Run the complete release-candidate story from the repository root with the
project's established Python 3.10 runtime:

```powershell
python -m benchmarks.run_stage26_product_acceptance
```

The command runs the full Stage 16 gate (including one real Qwen/llama.cpp API
inference), all frontend tests, the production build, the compressed bundle
gate, and an isolated deterministic browser flow. It allocates random loopback
API/preview ports, a unique temporary SQLite database, and a unique Agent Browser
session. It owns and stops only the processes it creates.

For Stage 26 script development only, skip inherited regressions while retaining
the browser, policy, failure, and restart checks:

```powershell
python -m benchmarks.run_stage26_product_acceptance --skip-regressions --output data/stage26-quick.json
```

This shortcut is not release evidence. A retained release candidate must omit
`--skip-regressions` and is written under `benchmarks/results/`. The browser
driver is pinned as an exact development dependency and can be run by the
acceptance orchestrator through `npm run verify:stage26:browser`; its required
target/session environment is supplied by the orchestrator.

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

SQLite schema migration is applied automatically on store open. Frontend
type-checking is part of the build. Stage 26 now declares a purpose-built browser
product-verification runner; a separate formatter, linter, visual-regression
suite, and coverage threshold remain undefined because no approved requirement
justifies them.

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

## Stage 27 portfolio release

Validate the recruiter/interviewer release from the repository root:

```powershell
python scripts\validate_portfolio_release.py
```

The command validates the strict manifest, required README headings, every local
Markdown link in the declared documents, screenshot PNG headers/dimensions, and
exact claims against retained JSON evidence. It writes a timestamped result to
`benchmarks/results/stage27-portfolio-release-*.json` and exits nonzero when the
release is incomplete or a claim has drifted.

Rebuild the five product screenshots while a matching backend and frontend are
running:

```powershell
cd apps\web
npm run capture:portfolio
```

Set `PORTFOLIO_WEB_BASE` when the owned workbench is not on port 4173. The driver
uses the project-pinned browser, creates one deterministic task, follows its ID
through the workbench, and fails if the Runtime capture boundary displays an API
error. Screenshots prove the browser integration story; real-model proof remains
the separate retained Stage 26 acceptance result.
