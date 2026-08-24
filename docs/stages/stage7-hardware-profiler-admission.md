# Stage 7 — Hardware Profiler & Memory-Aware Admission

## What this stage is for

Stage 7 decides whether the currently configured local-model workload is safe to
submit. It turns hardware capacity, live RAM/VRAM pressure, model metadata, an
explicit estimator, and retained measurements into a decision before the
scheduler or inference backend can run.

## Component upgrade map

| Component | Upgrade | What it does now |
| --- | --- | --- |
| Hardware profiler | New source-aware live snapshot | Reads CPU identity/logical processors, RAM capacity/availability, NVIDIA GPU/VRAM pressure, utilization, temperature, driver, and compute capability |
| Evidence model | Confidence/source/warnings on readings | Preserves unavailable physical-core data instead of converting 16 logical processors into a fabricated physical count |
| Model profile | Validated file-backed metadata | Records the actual 1,065.560 MiB GGUF size, quantization, 28 layers, context, and offload baseline |
| Memory estimator | Transparent conservative formula | Separates model-weight, context, and fixed components for host RAM and VRAM |
| Calibration comparison | Prediction-versus-measurement record | Compares the formula with the retained Stage 6 1,339.227 MiB RAM / 1,219 MiB VRAM observation |
| Admission policy | Six typed actions | Produces `ACCEPT`, `QUEUE`, `REDUCE_CONTEXT`, `REDUCE_GPU_OFFLOAD`, `FALLBACK`, or `REJECT_UNSAFE` with reasons and recommendations |
| Safety reserves | 2,048 MiB host and 512 MiB VRAM | Keeps configured headroom outside the predicted workload allocation |
| Agent runtime gate | New pre-scheduler boundary | Records `admission.evaluated`; only `ACCEPT` can transition to execution and scheduler submission |
| State machine | `RESOURCE_BLOCKED` terminal state | Separates pre-execution resource control from a backend OOM |
| Hardware CLI | Live plus controlled report | Shows this machine's decision and deterministic evidence for all six policy branches |

## Estimator and measured comparison

For the pinned Qwen 1.5B Q4_K_M configuration at 2,048 context and 28 GPU
layers, the estimator predicted 1,461.870 MiB host RAM and 1,236.116 MiB VRAM.
The retained real run observed 1,339.227 MiB peak child RAM and 1,219 MiB VRAM
delta. Prediction was higher by 122.643 MiB (9.158%) and 17.116 MiB (1.404%).

This is one calibration point. It supports a conservative decision for the
exact baseline; it does not validate linear scaling for other models or prove
that reserves prevent every OOM.

## Runtime boundary

`QUEUE` means capacity may be safe after current pressure clears. Stage 7 does
not place such a request into the execution scheduler because that would bypass
resource re-evaluation. Reduction and fallback actions are also recommendations:
Stage 8 will apply alternate inference parameters, while Stage 9 owns model
registry and fallback routing.

## Verification evidence

- 66 standard-library tests passed in 2.091 seconds, including all six policy outcomes, unknown
  telemetry rejection, actual model-file metadata, profiler parsing, calibration,
  active/profile mismatch rejection, pre-scheduler ordering, and backend
  non-invocation for non-accept decisions.
- Live snapshot: Ryzen 7 5800H, 16 logical processors, 32,097.656 MiB RAM,
  16,618.473 MiB available, RTX 3050 Laptop GPU, 4,096 MiB VRAM, 3,962 MiB free;
  profiler boundary 72.267 ms.
- The live baseline decision was `ACCEPT` with medium estimator confidence.
- A real admitted Qwen task then completed: 1,898.729 ms backend total,
  1,332.861 ms TTFT, 111.59 tokens/second, 1,339.113 MiB peak RAM, and
  1,219 MiB VRAM delta.
- Controlled scenarios demonstrated all six actions and are explicitly labeled
  synthetic rather than hardware measurements.

## Boundaries and debt

- Physical core count remains unavailable to the process; the declared 8-core
  constraint is retained in environment documentation but not emitted as live fact.
- Device-wide `nvidia-smi` pressure can include unrelated processes.
- The estimator has one model/configuration calibration point.
- Admission state is process-local and a blocked request is not automatically retried.
- Adaptation and fallback execution are deliberately deferred to Stages 8 and 9.
