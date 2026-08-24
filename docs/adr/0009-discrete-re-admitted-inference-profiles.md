# ADR-0009: Discrete, re-admitted inference resource profiles

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 7 can recommend context or GPU-offload reductions but intentionally does
not mutate the active llama.cpp configuration. Arbitrary continuous tuning would
be hard to validate and could silently create configurations that were never
measured. The current backend starts a fresh native process for every request,
so request-scoped native flags are directly inspectable.

## Decision

Define a small tracked catalog of named `InferenceProfile` values controlling
context size, logical and physical batch size, generation and prompt-processing
threads, GPU layers, flash attention, and device selection. Preserve the exact measured Stage 7
configuration as `performance`; add `balanced`, `constrained`, and `cpu_safe` as
explicit experimental hypotheses rather than claimed optima.

Select profiles in declared workload-specific order. Capture one fresh hardware
snapshot, estimate and admit each candidate against that same snapshot, and
choose only the first `ACCEPT`. Never pass a reduction recommendation directly
to native inference. Emit the complete attempts, selected profile, hardware,
admission, reason, and exact applied profile in lifecycle/result metadata.

Benchmark every profile with the same pinned model, prompt, seed, token cap,
backend build, and measurement path. Retain measurements and caveats. The
controller adapts one model only; model selection remains Stage 9.

## Consequences

- Stage 7 recommendations can now become a tested discrete configuration.
- Every applied profile is re-admitted before scheduler submission.
- Standard/interactive work prefers the measured all-GPU baseline; background
  work prefers the lower-VRAM balanced profile.
- Missing GPU telemetry can select `cpu_safe`; missing RAM admits no profile.
- Several parameters vary together, so the current benchmark demonstrates
  profile behavior but cannot attribute causality to one flag.
- The first zero-layer experiment still measured 311 MiB device VRAM. Adding
  explicit `--device none` reduced the repeated CPU-safe VRAM delta to 0 MiB,
  at the cost of higher host RAM and latency.

## Alternatives considered

- Mutate exact estimator recommendations: rejected until combinations are
  validated and bounded as profiles.
- Search every parameter combination online: rejected as costly and likely to
  overfit a tiny workload.
- Let llama.cpp `--fit` change settings invisibly: rejected because Stage 8
  needs inspectable decisions; the backend retains `--fit off`.
- Tune KV-cache types and multi-GPU split settings now: deferred because this is
  a single-GPU baseline and no isolated experiment currently justifies them.
- Route to another model: deferred to the Stage 9 registry and router.
