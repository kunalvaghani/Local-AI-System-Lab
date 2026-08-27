# Benchmark Methodology and Results

## Measurement philosophy

Every performance claim follows baseline → hypothesis → change → repeated or
controlled measurement → keep/revert. Configuration and thresholds are tracked
before release evaluation. One-run API/browser timings are labelled integration
evidence rather than throughput or field-performance claims.

## Inference baseline

Stage 2 ran five cold subprocess executions through the owned llama.cpp adapter
using the pinned Qwen2.5 1.5B Q4_K_M artifact. It retained model load, prompt
processing, time to first token, generation throughput, total time, peak child
working set, and device-wide VRAM delta.

| Metric | Stage 2 median |
| --- | ---: |
| Model load | 1,128.28 ms |
| TTFT | 1,686.85 ms |
| Generation | 115.81 tokens/s |
| Total | 2,572.26 ms |
| Peak process RAM | 1,339.02 MiB |
| VRAM delta | 1,219 MiB |

Source: [retained Stage 2 evidence](../../benchmarks/results/stage2-baseline-20260823T180550Z.json).

## Resource-profile experiment

Stage 8 applied four tracked profiles to the same model/workload family and
re-ran admission for each exact configuration.

| Profile | Tokens/s | VRAM delta | Interpretation |
| --- | ---: | ---: | --- |
| Performance | 100.92 | 1,189 MiB | Fastest GPU-heavy tracked profile |
| Balanced | 54.97 | 909 MiB | Lower VRAM with material throughput cost |
| Constrained | 40.41 | 527 MiB | Stronger pressure response |
| CPU-safe | 27.06 | 0 MiB | Explicit `--device none`; highest latency/host-memory tradeoff |

The first CPU-safe attempt used zero GPU layers but still initialized 311 MiB
VRAM. That configuration was rejected and explicit device isolation was kept.
Source: [final Stage 8 comparison](../../benchmarks/results/stage8-profile-comparison-20260824T122355Z.json).

## Product release result

Stage 26 combined the real-model backend gate and deterministic browser product
flow. The real call passed predeclared limits of at least 75 tokens/s, no more
than +50% TTFT regression, at most 1,600 MiB peak process RAM, at most 1,500 MiB
VRAM delta, and at most 10 seconds for the real API stream.

| Metric | Stage 26 actual | Release limit | Result |
| --- | ---: | ---: | --- |
| TTFT | 1,801.341 ms | ≤2,530.276 ms | PASS |
| Generation | 103.47 tokens/s | ≥75 | PASS |
| Total inference | 2,408.659 ms | Reported, no separate gate | EVIDENCE |
| Peak process RAM | 1,343.680 MiB | ≤1,600 MiB | PASS |
| VRAM delta | 1,189 MiB | ≤1,500 MiB | PASS |
| Browser product journey | 65,656.979 ms | ≤120,000 ms | PASS |
| Safe tool | 2.531 ms | ≤1,000 ms | PASS |
| JavaScript gzip | 150,997 bytes | ≤256,000 bytes | PASS |

The local Chromium sample reported 2.5 ms TTFB, 76 ms FCP/LCP, and CLS 0.01.
INP was unavailable. These values are not field Core Web Vitals.

## Reliability and security results

- Chaos: 9/9 expected outcomes, 1/1 killed-worker recovery, 8/9 containment.
  The uncontained database-result fault is the accepted terminal/output atomicity gap.
- Security: 14/14 bounded deterministic defenses held, zero reported failures,
  zero real model calls, database integrity `ok`.
- Product: 154 backend tests, 39 frontend tests, all required categories passed,
  release candidate true, overall maturity `PARTIAL`.

Sources: [chaos evidence](../../benchmarks/results/stage13-chaos-20260824T193424Z.json),
[security evidence](../../benchmarks/results/stage14-security-20260824T203349Z.json),
and [product acceptance](../../benchmarks/results/stage26-product-acceptance-20260827T101438Z.json).

## Methodological limits

- Cold subprocess inference differs from a persistent model server.
- Short samples do not characterize sustained thermals or concurrent workloads.
- Device-wide GPU sampling may include unrelated allocations.
- One installed real model cannot validate routing quality across model families.
- Completion and structural output validation do not establish semantic quality.
- Browser timings come from a local preview and automation harness, not real users.
