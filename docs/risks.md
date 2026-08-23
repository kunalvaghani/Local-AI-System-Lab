# Initial Risk Register

This register began in Stage 0 and is updated with evidence at each stage. A
planned mitigation is not an implemented control.

| ID | Risk | Likelihood | Impact | Current evidence | Planned response / owning stage |
| --- | --- | --- | --- | --- | --- |
| R-01 | 4 GB VRAM causes model load or context OOM | High | High | GPU has 4,096 MiB total | Measure a small GGUF baseline (2); conservative admission (7); adaptive config (8) |
| R-02 | RAM/VRAM estimator diverges from real use | High | High | No estimator or measurements exist | Compare predictions with observed deltas and retain error bounds (7) |
| R-03 | Python concurrency blocks cancellation or shutdown | Medium | High | Stage 1 runtime is synchronous; shutdown is tested, concurrency/cancellation are absent | Add cancellation foundations (2–3); scheduler concurrency tests (6) |
| R-04 | Framework abstractions hide core runtime behavior | Medium | High | Stage 1 core uses stdlib protocols with no framework dependency | Keep core contracts framework-independent; ADR review at each integration |
| R-05 | Unrestricted tools expose host files/processes/secrets | High | Critical | No tool runtime exists | Default-deny policy and restricted executor (5); adversarial suite (14) |
| R-06 | Nondeterministic model output is misrepresented as replayable | High | High | No trace schema exists | Separate deterministic events from generation metadata/hashes (11) |
| R-07 | SQLite contention or crash semantics lose task state | Medium | High | Persistence not implemented | Transactions, checkpoints, restart tests, and documented guarantees (10) |
| R-08 | Benchmarks become cherry-picked or non-reproducible | Medium | High | No benchmark harness exists | Version workloads/configs and report environment/distributions (2 onward) |
| R-09 | Python version ambiguity causes irreproducible installs | Medium | Medium | `requires-python >=3.10` is declared; machine still has 3.10/3.11 entry points | Use `python` consistently; lock dependencies when dependencies are introduced |
| R-10 | llama.cpp/CUDA setup delays real inference | Medium | High | `llama-cli` and `nvcc` absent from PATH | Prefer verified prebuilt binaries first; document/install only in Stage 2 |
| R-11 | Ollama prototype behavior is mistaken for flagship backend behavior | Medium | Medium | Client exists; service unreachable | Keep adapters distinct and benchmark the llama.cpp path (2) |
| R-12 | Frontend work outruns or fabricates backend capabilities | Medium | High | No frontend/backend exists | Enforce Stage 16 acceptance before production frontend work |
| R-13 | Scope growth creates interfaces for unimplemented future features | High | Medium | Stage 1 protocols expose only demonstrated lifecycle methods | Continue one-stage gate and require a test/capability for interface growth |
| R-14 | Observability overhead distorts constrained-device performance | Medium | Medium | No telemetry exists | Benchmark overhead and sampling/retention choices (12) |
| R-15 | Access-restricted hardware APIs reduce profiler fidelity | Medium | Medium | CIM/systeminfo denied during Stage 0 | Layer fallbacks and expose confidence/source with every reading (7) |

## Review rule

At each stage boundary, update evidence, add newly discovered risks, and change
likelihood/impact only when there is a stated reason. Closed risks remain in the
record with the verification that justified closure.
