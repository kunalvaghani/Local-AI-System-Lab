# Current Project State

## Active Project

Local AI Systems Lab — a fully local, inspectable AI runtime/platform for constrained consumer hardware.

## Current Milestone

Reproducible real local inference established; waiting at the Stage 2 approval gate.

## Current Stage

Stage 2 — Local Inference Baseline — COMPLETE, AWAITING APPROVAL.

## Current Subsystem

Pinned llama.cpp/GGUF inference, streaming, owned-process cancellation, inference metrics, and reproducible benchmarking.

## Last Completed Work

- Pinned llama.cpp Windows CUDA release `b10566` / commit `bb4caa7540188872173c44d161602d9271386413` with verified archives and executable.
- Pinned `Qwen/Qwen2.5-1.5B-Instruct-GGUF` Q4_K_M at revision `91cad51170dc346986eccefdc2dd33a9da36ead9` with verified model SHA-256.
- Added an idempotent PowerShell setup path; native/model artifacts remain ignored.
- Implemented a framework-independent `llama-completion` adapter with ChatML prompting, offline execution, incremental streaming, one-process ownership, and structured cancellation.
- Added parsing/sampling for model load, startup, TTFT, prompt evaluation, generation throughput, total time, peak process RAM, and coarse device VRAM delta.
- Preserved the Stage 1 deterministic backend and propagated optional inference metrics through typed results.
- Added a real inference CLI, five-prompt workload, reproducible benchmark runner, raw result, report, and ADR-0003.
- Expanded the standard-library suite from 13 to 19 passing tests.

## Currently Working On

None. Stage 2 is complete and work is stopped at the mandatory approval gate.

## Current Blockers

- User approval is required before Stage 3.
- No technical blocker remains for the demonstrated Stage 2 baseline.

## Important Decisions

- Follow one stage at a time and stop for explicit approval after each stage.
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

See [ADR-0001](docs/adr/0001-stage-gated-modular-backend-first.md), [ADR-0002](docs/adr/0002-typed-protocols-and-stdlib-skeleton.md), and [ADR-0003](docs/adr/0003-pinned-llama-cpp-qwen-baseline.md).

## Tests Passing

- `pwsh -NoProfile -File .\scripts\setup_stage2.ps1` — hashes, llama.cpp version, and CUDA device verified; idempotent rerun passed.
- `python -m unittest discover -s tests -v` — 19 tests passed in 1.650 seconds in the final gate run.
- `python -m benchmarks.run_stage2_baseline --runs-per-prompt 1` — five real prompts completed and a tracked JSON result was written.
- Real CLI generation returned coherent local text and complete metrics with one real LLM call.
- Real `--cancel-after-ms 1800` run returned structured cancellation with exit code 130; a follow-up GPU check showed 0 MiB in use.
- `python -m compileall -q runtime tests benchmarks` — exit 0.
- `python -m pip install --dry-run --no-deps --no-build-isolation .` — would install `local-ai-systems-lab-0.2.0`, exit 0.
- `python -m runtime --objective "Stage 2 regression smoke task"` — four-event stub lifecycle remained intact, exit 0.
- `git diff --check` — exit 0 with only Git's Windows LF-to-CRLF working-copy warnings.
- Local Markdown link verification — all links across 13 Markdown files resolved, exit 0; all 15 required state headings were present.

## Known Problems

- The scheduler executes immediately on the caller thread; it has no queue, priority, timeout, cancellation, starvation, or concurrency behavior.
- The real backend reloads the model for every request, making median cold TTFT about 1.69 seconds.
- The backend accepts only one active inference per instance; runtime task cancellation is not yet integrated with scheduler semantics.
- VRAM is sampled at 200 ms via total-device `nvidia-smi` data and can include unrelated GPU use.
- The five-prompt, single-iteration sample is acceptance evidence, not a statistically strong performance claim.
- A 64-token cap truncated some longer answers; one JSON-only prompt included Markdown fences, so no broad quality claim is made.
- Routing is static and the identity policy is not a security sandbox.
- Checkpoints and metric events are process-local, non-durable, and make no thread-safety guarantee.
- Admission control, tools, persistence, replay, API, and frontend do not exist; full hardware profiling remains Stage 7 work.
- No Python dependency lock is necessary while project dependencies remain empty; revisit this when a Python dependency is introduced.
- WMI/CIM hardware queries are access-restricted in the current execution context; the environment checker uses narrower registry/.NET/NVIDIA queries.
- The Windows registry product label reports `Windows 10 Home Single Language` while build/display-version evidence is `26200.9168` / `25H2`; the report preserves the raw evidence rather than inferring a marketing name.
- The installed Hugging Face CLI 0.36.0 lacks newer `hf models info`/dry-run forms; exact Hub revision metadata and the pinned download path were used instead.
- The first benchmark file-path invocation failed to import `runtime`; the benchmark became a package and the documented module invocation passed.

## Performance Baseline

On five cold-process runs: median model load 1,128.28 ms; median TTFT 1,686.85 ms; median prompt throughput 991.23 tokens/second; median generation throughput 115.81 tokens/second; median total request time 2,572.26 ms; median peak child-process RAM 1,339.02 MiB; and observed VRAM delta 1,219 MiB. See [the Stage 2 report](docs/benchmarks/stage2-local-inference-baseline.md) and [raw result](benchmarks/results/stage2-baseline-20260823T180550Z.json).

## Backend Acceptance Status

NOT STARTED. The Backend Acceptance Gate is Stage 16.

## Frontend Research Status

NOT STARTED. Production frontend work remains prohibited until backend acceptance. Stage 17 research is also not current-stage work.

## Next Step

Stage 3 — Agent Runtime MVP

## Later Backlog

Stages 3–27 remain intentionally deferred and must be entered one at a time after explicit approval.
