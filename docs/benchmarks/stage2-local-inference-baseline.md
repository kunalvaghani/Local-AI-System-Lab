# Stage 2 Local Inference Baseline

## Outcome

Real GGUF inference completed locally on the RTX 3050 Laptop GPU. Five cold
process runs generated non-placeholder text, with median generation throughput
of 115.81 tokens/second and median process-launch-to-first-text latency of
1,686.85 ms.

## Reproduction

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
python -m benchmarks.run_stage2_baseline --runs-per-prompt 1
```

The tracked workload is
[`../../benchmarks/prompts/stage2-baseline.json`](../../benchmarks/prompts/stage2-baseline.json),
the exact configuration is
[`../../configs/inference-baseline.json`](../../configs/inference-baseline.json),
and the raw result is
[`../../benchmarks/results/stage2-baseline-20260823T180550Z.json`](../../benchmarks/results/stage2-baseline-20260823T180550Z.json).

## Fixed environment

| Item | Value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU, 4,096 MiB |
| Driver | 610.74 |
| Python | 3.10.6, 64-bit |
| llama.cpp | build `b10566`, commit `bb4caa754` |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M, Apache-2.0, 1,117,320,736 bytes |
| Context / batch | 2,048 / 256 |
| CPU threads | 8 |
| GPU layers / flash attention | all / on |
| Sampling | temperature 0, seed 42, maximum 64 generated tokens |

## Measurements

| Metric | Minimum | Median | P95 nearest-rank / maximum |
| --- | ---: | ---: | ---: |
| Model load | 1,119.92 ms | 1,128.28 ms | 1,191.07 ms |
| Startup to ready | 1,610.15 ms | 1,630.84 ms | 1,694.45 ms |
| Time to first text | 1,662.57 ms | 1,686.85 ms | 1,752.20 ms |
| Prompt evaluation | 51.82 ms | 54.07 ms | 56.99 ms |
| Prompt throughput | 789.58 tok/s | 991.23 tok/s | 1,220.66 tok/s |
| Generation throughput | 114.44 tok/s | 115.81 tok/s | 117.14 tok/s |
| Total request time | 2,219.63 ms | 2,572.26 ms | 2,636.95 ms |
| Peak process RAM | 1,338.97 MiB | 1,339.02 MiB | 1,339.27 MiB |
| Device VRAM delta | 1,219 MiB | 1,219 MiB | 1,219 MiB |

Each request launched a new process and reloaded the model, so TTFT is a cold
baseline. `model_load_ms` is derived from llama.cpp log-clock markers. RAM is
the child process peak working set. VRAM is a 200 ms `nvidia-smi` total-device
sample, so unrelated GPU activity can affect it. Five heterogeneous prompts
are useful acceptance evidence but not a statistically strong distribution.
The raw result records parent commit `e1078fb` and `git_worktree_clean: false`
because Stage 2 source/config changes were intentionally still uncommitted when
the acceptance run was captured.

## Streaming and cancellation evidence

The backend yields incremental text chunks before a final metrics chunk. Unit
tests exercise chunk boundaries and the UI end-marker cleanup. A live run was
cancelled after 1,800 ms: the CLI returned structured `inference_cancelled`
with exit code 130; 750 ms later `nvidia-smi` reported 0 MiB used and no active
inference process, demonstrating subprocess cleanup and VRAM release.

## Output quality note

All five prompts produced coherent local output, but a 64-token cap truncated
some longer answers and one structured-output response included Markdown fences
despite asking for only JSON. Stage 2 establishes inference mechanics and a
performance baseline; it does not claim instruction-following quality.
