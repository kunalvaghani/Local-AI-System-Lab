# Stage 9 — Model Registry, Router & Compute Budgets

## What this stage is for

Stage 9 turns model selection into an explicit runtime decision and limits the
compute a task may consume. It sits before scheduler submission so an unavailable,
incapable, oversized, or over-budget route cannot silently reach native inference.

## Component upgrade map

| Component | What it does in Stage 9 | Upgrade over Stage 8 |
| --- | --- | --- |
| Model registry | Validates model identity, local artifact, backend support, capabilities, token limits, minimum memory, and benchmark provenance | Replaces the implicit single-model assumption with inspectable availability |
| Workload router | Classifies task type/complexity and scores every safe candidate from workload, latency, queue, hardware, budget, and benchmark evidence | Replaces the static model ID with an explained candidate decision |
| Compute-budget policy | Supplies interactive/standard/background defaults or accepts a typed task override | Introduces explicit call, token, time, RAM, and VRAM constraints |
| Runtime budget gate | Caps generated tokens and scheduler time; rejects zero-call or estimated-memory violations before submission | Prevents a selected route from bypassing task-level compute limits |
| Adaptive controller | Re-admits the exact profile after routing | Remains the final model/profile memory-safety authority |
| Result/lifecycle evidence | Records the full route, candidate reasons, resolved budget, enforced fields, and observed usage | Makes routing and budget behavior auditable per task |

## Implemented behavior

- `configs/model-registry.json` declares the installed Qwen2.5 1.5B model and an
  optional Qwen2.5 0.5B candidate.
- Availability is derived from both `Path.is_file()` and `backend_configured`.
  The compact candidate is currently unavailable and has no fabricated benchmark.
- Candidate checks cover exact capability, context/output limits, minimum model
  memory, live RAM/VRAM, and task memory budgets.
- Candidate scores use task complexity, workload latency/efficiency preference,
  queue congestion, quality rank, and the retained Stage 8 benchmark when present.
- Workload defaults enforce one call; 64/64/32 maximum tokens for
  interactive/standard/background; 30/30/45 second task budgets; and explicit
  RAM/VRAM ceilings.
- Exact profile estimates are checked against task memory ceilings after the
  Stage 8 adaptive controller evaluates each candidate; a controlled 600 MiB
  VRAM budget skips performance/balanced and selects `constrained`.
- `local-ai-routing` / `python -m runtime.routing_cli` exposes live registry state,
  controlled two-model routes, a seven-token cap, and a zero-call rejection.

## Demonstrated output

Controlled router evaluation retained in
`benchmarks/results/stage9-routing-20260824T124057Z.json` selected:

- interactive explanation → optional compact 0.5B candidate;
- standard risk analysis → installed 1.5B candidate, because the compact model
  does not declare `risk_analysis`.

This is a routing-policy demonstration only. The compact record temporarily
reuses an existing file path and stub-compatible backend flag so availability
checks can execute; no compact model inference, quality, latency, or resource
measurement is claimed.

Live registry inspection found one available model. Both live workload routes
selected Qwen2.5 1.5B and explicitly rejected the compact candidate because its
artifact is not installed and no backend is configured.

Real Stage 9 interactive execution completed through all boundaries:

- route: installed Qwen2.5 1.5B;
- profile: `performance`;
- budget: one call, 64 generated tokens, 30 seconds, 2,048 MiB RAM, 1,536 MiB VRAM;
- actual generated runs: 32;
- task elapsed: 2,391.000 ms;
- backend total / TTFT: 2,142.737 / 1,445.427 ms;
- throughput: 106.54 tokens/s;
- peak child RAM / VRAM delta: 1,343.715 / 1,189 MiB.

Real background execution automatically used the `balanced` profile and the
32-token workload budget: 25 generated runs, 5,031.000 ms task elapsed,
4,795.147 ms backend total, 1,469.083 ms TTFT, 48.83 tokens/s, 1,351.633 MiB
peak child RAM, and 909 MiB VRAM delta.

## Verification

- Stage 9 focused suite: 9 tests passed, including VRAM-budget profile fallback.
- Final full suite: 88 tests passed in 2.898 seconds.
- `python -m runtime.routing_cli`: exit 0.
- `python -m benchmarks.run_stage9_routing`: exit 0 and retained result.
- Two real `runtime.agent_cli` runs: exit 0.
- Syntax compilation, 0.9.0 package dry run, deterministic stub smoke, and
  `git diff --check`: exit 0; line-ending notices only.

## Limits retained

- Only one real model artifact/backend is available, so real multi-model
  execution is not claimed.
- Model capability and quality ranks are declared policy metadata, not semantic
  output validation.
- Historical routing evidence is a one-run Stage 8 baseline.
- Memory ceilings are enforced against preflight estimates; postflight sampling
  reports observed peaks but cannot prevent an estimator miss in progress.
- Routing/budget state is process-local and will be owned by Stage 10 persistence.
