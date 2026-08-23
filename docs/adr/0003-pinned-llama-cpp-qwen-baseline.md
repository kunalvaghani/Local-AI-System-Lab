# ADR-0003: Pinned llama.cpp subprocess and Qwen GGUF baseline

- Status: Accepted
- Date: 2026-08-23

## Context

Stage 2 requires real, fully local generation with streaming, cancellation,
measured performance, and reproducible artifacts on a 4 GB RTX 3050 Laptop
GPU. The implementation must preserve the Stage 1 inference protocol and avoid
making a model server or orchestration framework part of the core runtime.

## Decision

Use the Windows CUDA 12.4 build of llama.cpp release `b10566` (commit
`bb4caa7540188872173c44d161602d9271386413`) and the pinned Q4_K_M GGUF from
`Qwen/Qwen2.5-1.5B-Instruct-GGUF` revision
`91cad51170dc346986eccefdc2dd33a9da36ead9`. Verify downloaded archives, the
executable, and model with committed SHA-256 values.

The adapter launches one offline `llama-completion` subprocess per request,
uses raw Qwen ChatML, streams stdout, parses llama.cpp timing logs, samples
process RAM and device VRAM, and owns subprocess termination for cancellation.
Only one request may execute per backend instance.

## Alternatives considered

| Alternative | Result | Reason |
| --- | --- | --- |
| Ollama | Rejected for this baseline | A convenient service adapter, but it would hide the native invocation and was not reachable during inspection |
| `llama-cpp-python` | Deferred | Adds a Python/native package compatibility surface without being needed for the first measurable path |
| Long-running `llama-server` | Deferred | Would improve warm-request latency, but introduces service lifecycle and protocol work better measured against this cold baseline |
| Link llama.cpp directly from C++ | Rejected now | No profiled bottleneck justifies a native project layer |
| Per-request `llama-completion` | Selected | Small, inspectable adapter with direct streaming/cancellation and no resident service |

## Consequences

- Generation is real, local, framework-independent, and artifact-verifiable.
- Cold TTFT includes model reload on every request and is therefore not a
  production latency target.
- Cancellation can terminate and reap the exact owned process.
- VRAM measurement is coarse total-device sampling and may include unrelated
  GPU activity.
- A persistent backend remains a future optimization that requires a new
  benchmark and lifecycle decision.

## Evidence

- [`../../configs/inference-baseline.json`](../../configs/inference-baseline.json)
- [`../benchmarks/stage2-local-inference-baseline.md`](../benchmarks/stage2-local-inference-baseline.md)
- [`../../benchmarks/results/stage2-baseline-20260823T180550Z.json`](../../benchmarks/results/stage2-baseline-20260823T180550Z.json)
