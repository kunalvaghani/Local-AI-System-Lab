# Stage 22 — Hardware & Performance Lab UI

## Stage Completed

Stage 22 turns accepted hardware, observability, model, scheduler, and task
contracts into a visual local performance laboratory. It is for investigating
how resource pressure and inference behavior relate while workloads execute. It
stops before Stage 23 Chaos & Security Lab UI.

## Expected Output

- CPU, RAM, GPU, and VRAM visualization.
- TTFT, tokens/second, queue delay, scheduler throughput, and distributions.
- Model selection, exact reported configuration, and workload budgets.
- Bounded historical trends with honest source/sample boundaries.
- Live refresh without fabricating continuous telemetry.

## Actual Output

| Component | What it does | Stage 22 upgrade |
| --- | --- | --- |
| Capacity board | Shows CPU topology, RAM pressure, GPU utilization/temperature, and VRAM pressure with source/confidence | Replaces hardware placeholders with real profiler evidence |
| Performance signals | Resolves selected-task, sampled P50, or matching retained benchmark TTFT/throughput and queue evidence | Makes source precedence and missing samples explicit |
| Scheduler throughput | Shows completed/submitted work from the current process | Connects throughput to the accepted scheduler snapshot |
| Distribution table | Shows N, P50, P95, max, and unit for eight latency/resource metrics | Exposes the 60-minute statistical envelope without zero-filling |
| Configuration panel | Shows selected model, profile, context, batch, threads, GPU layers, device, and workload budget when reported | Connects applied configuration to performance evidence |
| Recent workload trend | Compares duration and exact task metrics for at most eight durable recent tasks | Adds bounded historical context without claiming continuous sampling |
| Model candidates | Shows availability, quantization, size, latency class, retained benchmark, and profile | Separates registered candidates from live task selection |
| Query ownership | Polls metrics with `live=false` while hardware/scheduler retain dedicated owners | Removes duplicate expensive live hardware profiling |

## New Demonstrable Capability

An operator can inspect measured CPU/RAM/GPU/VRAM state, see the selected or
retained inference envelope, compare queue and scheduler behavior, inspect exact
reported model/profile configuration, and relate recent task durations without
leaving the local workbench.

## Files Added

- `apps/web/src/components/performance/PerformanceLab.tsx`
- `apps/web/src/styles/performance.css`
- `apps/web/scripts/stage22-smoke.mjs`
- `benchmarks/results/stage22-hardware-performance-20260825T133404Z.json`
- `docs/adr/0022-source-labelled-performance-projection.md`
- `docs/stages/stage22-hardware-performance-lab-ui.md`

## Files Modified

- Frontend API types/client, route composition, identity, fixtures, component
  tests, package manifest, and lockfile under `apps/web/`.
- `README.md`, `PROJECT_STATE.md`, and development, architecture, repository,
  ADR-index, and risk documentation under `docs/`.

## Tests Performed

- 23 frontend component tests, including six route-specific automated axe scans.
- Hardware source/meter/null handling, metric precedence/distributions, model
  availability/budget, and bounded trend coverage.
- Real Vite proxy/API hardware, model, scheduler, task, and metrics smoke.
- 150 backend regression tests and Python compile validation.
- Production TypeScript/Vite build, gzip bundle gate, and diff hygiene checks.

## Measurements

- Real hardware profile: 789.314 ms; Ryzen 7 5800H, 16 logical processors,
  32,097.656 MiB RAM, RTX 3050 Laptop GPU, 4,096 MiB VRAM.
- Real smoke evidence retrieval: 802.412 ms; complete smoke: 1,610.033 ms.
- Stub workload: completed; 0 ms inference total, null TTFT/token throughput,
  0 ms queue wait, 62.956 ms scheduler execution.
- Durable metrics: one task/queue/task-duration sample, zero TTFT/token-rate
  samples, 7.058 ms collection.
- Registry evidence: retained Qwen performance TTFT 1,655.1855 ms and 100.92
  tokens/second, correctly separate from the stub task.
- Frontend tests: 23/23, 7.95 seconds test time; backend tests: 150/150,
  40.544 seconds.
- Production build: 217 modules; 127,686 gzip JavaScript bytes (49.9% of the
  256,000-byte gate) and 7,365 gzip CSS bytes.

## Expected vs Actual

| Requirement | Expected | Actual |
| --- | --- | --- |
| CPU/RAM/GPU/VRAM | Visualize current resources | Delivered with source/confidence and explicit CPU-utilization boundary |
| TTFT/tokens per second | Investigate measured inference | Delivered with task → sampled P50 → matching retained precedence |
| Queue delay/throughput | Show scheduling behavior | Delivered from task/distribution and current scheduler snapshot |
| Model/configuration | Explain selection and applied setup | Delivered when task metadata reports it; otherwise unavailable |
| Historical trends | Compare prior behavior | Delivered for the bounded eight-task API response, not a continuous series |
| Missing data | Preserve null semantics | Delivered; unavailable meters are not semantic zero |
| Polling cost | Avoid redundant profiling | Delivered by using durable-only metrics plus dedicated live owners |

## Problems / Technical Debt

- CPU utilization is not exposed; only model/topology evidence is available.
- Historical trends are recent task summaries, not continuous hardware samples.
- The API has no versioned experiment-comparison or configuration-catalog view.
- Stub inference legitimately has no TTFT or token-throughput sample.
- Manual computed-contrast, forced-color, zoom/reflow, and screen-reader checks
  remain outside automated jsdom coverage.
- Windows development teardown can still log tracked disconnected-client
  tracebacks while active polls are aborted.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` records Stage 22 complete, query/provenance decisions,
measurements, limitations, evidence, and the Stage 23 approval gate.

## Next Stage

Stage 23 — Chaos & Security Lab UI. No Stage 23 implementation was started.
