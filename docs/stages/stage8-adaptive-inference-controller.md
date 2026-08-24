# Stage 8 — Adaptive Inference Controller

## What this stage is for

Stage 8 converts hardware/admission evidence into an exact llama.cpp resource
configuration. It chooses among bounded, inspectable profiles, re-admits the
chosen candidate, applies its native flags, and retains measurements showing the
latency/memory tradeoff.

## Component upgrade map

| Component | Upgrade | What it does now |
| --- | --- | --- |
| `InferenceProfile` | New typed native-resource contract | Names purpose, context, batch/ubatch, generation/batch threads, GPU layers, flash attention, and device selection |
| Profile catalog | Four tracked experimental profiles | Provides performance, balanced, constrained, and zero-offload CPU-safe hypotheses plus workload order |
| Adaptive controller | Workload-ordered candidate evaluation | Uses one fresh snapshot, re-estimates each candidate, and selects only the first `ACCEPT` |
| Admission integration | Profile-specific re-admission | Prevents a recommendation or unmeasured mutation from bypassing the Stage 7 gate |
| Agent runtime | Controller boundary and lifecycle event | Records all attempts and passes the selected profile into `InferenceRequest` before scheduling |
| llama.cpp backend | Request-scoped native flags | Applies exact profile values to `--ctx-size`, `--batch-size`, `--ubatch-size`, `--threads`, `--threads-batch`, `--gpu-layers`, `--flash-attn`, and `--device` |
| Inference metadata | Applied-profile evidence | Returns the exact native profile with model output and metrics |
| Adaptive CLI | Live and controlled selection inspector | Shows workload choices, VRAM-pressure fallback, missing-GPU CPU-safe selection, and missing-RAM refusal |
| Benchmark runner | Same-workload profile comparison | Executes every profile through the real pinned Qwen/llama.cpp measurement path |

## Profile definitions

| Profile | Context | Batch/ubatch | Threads/batch threads | GPU layers | Device | Intended use |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| performance | 2048 | 256/256 | 8/8 | 28 | CUDA0 | Exact all-GPU measured baseline |
| balanced | 1536 | 192/192 | 8/8 | 20 | CUDA0 | Lower VRAM background/default pressure response |
| constrained | 1024 | 128/128 | 6/6 | 8 | CUDA0 | Substantial VRAM reduction when balanced does not fit |
| cpu_safe | 1024 | 64/64 | 8/8 | 0 | none | Explicit CPU device path when GPU capacity is unavailable |

These values are explicit hypotheses. They are neither universally optimal nor
independently causal because several variables change between profiles.

## Real same-workload comparison

One cold run per profile used the same Qwen model, prompt, seed, 32-token cap,
llama.cpp build, and sampler:

| Profile | TTFT ms | Total ms | Generation tok/s | Peak RAM MiB | VRAM delta MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| performance | 1655.185 | 2467.875 | 100.92 | 1343.355 | 1189 |
| balanced | 1469.025 | 2448.350 | 54.97 | 1351.406 | 909 |
| constrained | 1432.768 | 2594.512 | 40.41 | 1354.918 | 527 |
| cpu_safe | 1960.252 | 3581.382 | 27.06 | 1796.082 | 0 |

Observed against `performance`, `balanced` reduced VRAM by 280 MiB, constrained
by 662 MiB, and CPU-safe by 1,189 MiB. Performance had the highest generation
rate; constrained had the lowest TTFT in this final sample. One run per profile
is demonstration evidence, not a strong benchmark.

The first experiment used zero GPU layers without disabling the device and still
measured 311 MiB VRAM. The local llama.cpp help exposed `--device none`; adding
that explicit control produced a 0 MiB VRAM delta on the repeated CPU-safe run.
This kept change increased peak host RAM from 1,511.090 to 1,796.082 MiB and
total time from 3,000.478 to 3,581.382 ms. Both raw runs are retained.

## Estimate versus final measurement

Positive error means prediction exceeded the observed allocation; negative
error means the estimator underpredicted it:

| Profile | Predicted RAM | Observed RAM | RAM error MiB | Predicted VRAM | Observed VRAM | VRAM error MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| performance | 1461.870 | 1343.355 | +118.515 | 1236.116 | 1189 | +47.116 |
| balanced | 1441.390 | 1351.406 | +89.984 | 885.226 | 909 | -23.774 |
| constrained | 1420.910 | 1354.918 | +65.992 | 366.890 | 527 | -160.110 |
| cpu_safe | 1420.910 | 1796.082 | -375.172 | 0 | 0 | 0 |

The estimator is not uniformly conservative outside its calibrated baseline.
The separate 2,048 MiB host and 512 MiB device reserves covered every observed
underprediction in this sample, but that does not validate the formula for new
profiles or models. These extrapolated decisions remain low-confidence.

## Demonstrated runtime selection

- Live standard workload: `performance`, `ACCEPT`, then scheduler/backend.
- Live background workload: `balanced`, `ACCEPT`, then scheduler/backend.
- Controlled 1,500 MiB free VRAM: performance `QUEUE`, balanced `ACCEPT`.
- Controlled missing GPU: `cpu_safe` accepted after GPU profiles were rejected.
- Controlled missing RAM: all four profiles rejected; scheduler/backend untouched.

## Boundaries and debt

- The catalog is tied to one pinned Qwen model and one workstation class.
- Profile orders are policy baselines, not learned or globally optimal rankings.
- The one-run comparison is vulnerable to thermal, OS, and process variation.
- VRAM remains device-wide 200 ms sampling and can include unrelated allocations.
- Combined profile changes do not isolate individual parameter effects.
- Persistent serving, KV-cache experiments, automatic benchmark learning, and
  multi-model routing remain unimplemented.

## Verification evidence

- `python -m unittest discover -s tests -v`: 79 tests passed in 2.699 seconds.
- Thirteen Stage 8-focused tests passed profile/catalog validation, workload
  ordering, one-snapshot selection, pressure fallback, missing GPU/RAM,
  request-native flags, applied metadata, runtime ordering/blocking, CLI, and
  factory composition.
- `python -m runtime.adaptive_cli`: live and controlled selections matched the
  declared policy; exit 0.
- `python -m benchmarks.run_stage8_profiles --runs-per-profile 1`: exploratory
  and final four-profile runs completed; both raw comparisons were retained.
- Real standard and background agent executions completed through profile
  selection, re-admission, scheduler, and llama.cpp.
- Syntax compilation, 0.8.0 package dry run, deterministic stub regression, and
  `git diff --check` passed.
