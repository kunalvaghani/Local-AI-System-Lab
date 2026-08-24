# ADR-0008: Conservative pre-scheduler memory admission

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 6 controls execution order but cannot establish that a request fits current
host and device memory. On a 4 GB GPU, admitting from static capacity alone can
turn transient pressure or an oversized configuration into an avoidable OOM.
The available evidence is one measured Qwen configuration, not a universal
memory model.

## Decision

Profile CPU, logical cores, RAM availability, NVIDIA GPU, VRAM availability,
utilization, temperature, driver, and compute capability immediately before
scheduler submission. Every reading carries its source and confidence; missing
physical-core access remains unknown rather than inferred.

Use an inspectable linear estimator with model-file size, context, GPU-offload
fraction, fixed overheads, and explicit 2,048 MiB host / 512 MiB VRAM reserves.
Label the calibrated baseline medium-confidence and extrapolations low-confidence.
Compare its baseline prediction with the retained Stage 6 measured peak.

The gate emits `ACCEPT`, `QUEUE`, `REDUCE_CONTEXT`, `REDUCE_GPU_OFFLOAD`,
`FALLBACK`, or `REJECT_UNSAFE`. Only `ACCEPT` enters the scheduler in Stage 7.
Every other outcome ends in `RESOURCE_BLOCKED` with the full decision attached;
the caller must resubmit after pressure changes or a later controller/router
applies the recommendation.

## Consequences

- Unsafe or unadapted work cannot invoke the backend through the Stage 7 runtime.
- Decisions and arithmetic are machine-readable and interview-inspectable.
- `QUEUE` is an admission recommendation, not the Stage 6 execution queue.
- Live GPU evidence currently depends on `nvidia-smi`; no GPU means offload is
  reduced to zero only when that adaptation is allowed.
- One calibration run cannot validate other models, quantizations, contexts, or
  concurrent allocations. Safety reserves reduce risk but do not guarantee no OOM.

## Alternatives considered

- Admit from total capacity only: rejected because it ignores live pressure.
- Treat missing telemetry as zero pressure: rejected as unsafe fabrication.
- Automatically mutate llama.cpp parameters: deferred to measured Stage 8 work.
- Automatically route a fallback model: deferred to the Stage 9 registry/router.
- Add a hardware dependency: rejected because Windows APIs and `nvidia-smi`
  provide the required current evidence with no new package.
