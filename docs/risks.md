# Initial Risk Register

This register began in Stage 0 and is updated with evidence at each stage. A
planned mitigation is not an implemented control.

| ID | Risk | Likelihood | Impact | Current evidence | Planned response / owning stage |
| --- | --- | --- | --- | --- | --- |
| R-01 | 4 GB VRAM causes model load or context OOM | Medium | High | Pinned 1.5B Q4_K_M at 2,048 context completed five runs with 1,219 MiB observed VRAM delta; larger models/contexts remain untested | Conservative admission (7); adaptive config (8) |
| R-02 | RAM/VRAM estimator diverges from real use | High | High | No estimator or measurements exist | Compare predictions with observed deltas and retain error bounds (7) |
| R-03 | Python concurrency blocks cancellation or shutdown | Medium | High | Native subprocess cancellation passed fake-process tests and a live 1,800 ms cancellation with process/VRAM cleanup; scheduler-level cancellation remains absent | Integrate agent task cancellation (3); scheduler concurrency tests (6) |
| R-04 | Framework abstractions hide core runtime behavior | Medium | High | Stage 1 core uses stdlib protocols with no framework dependency | Keep core contracts framework-independent; ADR review at each integration |
| R-05 | Unrestricted tools expose host files/processes/secrets | High | Critical | No tool runtime exists | Default-deny policy and restricted executor (5); adversarial suite (14) |
| R-06 | Nondeterministic model output is misrepresented as replayable | High | High | No trace schema exists | Separate deterministic events from generation metadata/hashes (11) |
| R-07 | SQLite contention or crash semantics lose task state | Medium | High | Persistence not implemented | Transactions, checkpoints, restart tests, and documented guarantees (10) |
| R-08 | Benchmarks become cherry-picked or non-reproducible | Medium | High | Workload/config/raw five-run result and measurement caveats are tracked; sample is intentionally small | Expand repeat counts and comparative baselines only with declared hypotheses |
| R-09 | Python version ambiguity causes irreproducible installs | Medium | Medium | `requires-python >=3.10` is declared; machine still has 3.10/3.11 entry points | Use `python` consistently; lock dependencies when dependencies are introduced |
| R-10 | llama.cpp/CUDA setup delays real inference | Low | High | Idempotent setup verified pinned prebuilt archives, executable, model, version, and CUDA device; downloads remain large | Retain hashes and rerun setup on a clean machine before portability claims |
| R-11 | Ollama prototype behavior is mistaken for flagship backend behavior | Low | Medium | Stage 2 uses and labels a direct llama.cpp path; Ollama was not used | Keep future adapters and measurements distinct |
| R-12 | Frontend work outruns or fabricates backend capabilities | Medium | High | No frontend/backend exists | Enforce Stage 16 acceptance before production frontend work |
| R-13 | Scope growth creates interfaces for unimplemented future features | High | Medium | Stage 1 protocols expose only demonstrated lifecycle methods | Continue one-stage gate and require a test/capability for interface growth |
| R-14 | Observability overhead distorts constrained-device performance | Medium | Medium | No telemetry exists | Benchmark overhead and sampling/retention choices (12) |
| R-15 | Access-restricted hardware APIs reduce profiler fidelity | Medium | Medium | CIM/systeminfo denied during Stage 0 | Layer fallbacks and expose confidence/source with every reading (7) |
| R-16 | Per-request model reload dominates latency | High | Medium | Median model load was 1,128.28 ms and cold TTFT 1,686.85 ms | Compare a persistent server only after profiling and preserve this cold baseline |
| R-17 | Total-device VRAM sampling attributes unrelated GPU use to inference | Medium | Medium | Stage 2 samples `nvidia-smi` every 200 ms and observed a stable 1,219 MiB delta | Add process-aware/finer profiling where supported (7); keep source/caveat attached |

## Review rule

At each stage boundary, update evidence, add newly discovered risks, and change
likelihood/impact only when there is a stated reason. Closed risks remain in the
record with the verification that justified closure.
