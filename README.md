# Local AI Systems Lab

A stage-gated portfolio project for building an inspectable local AI runtime on
constrained consumer hardware. The runtime now has a reproducible, real local
GGUF inference backend in addition to its deterministic test stub.

## Current status

- Last completed stage: Stage 2 — Local Inference Baseline
- Next approval-gated stage: Stage 3 — Agent Runtime MVP
- Backend acceptance: NOT STARTED
- Frontend work: PROHIBITED until the backend acceptance gate passes

See [PROJECT_STATE.md](PROJECT_STATE.md) for the source-of-truth status.

## Run local inference

Python 3.10 or newer, PowerShell 7, the Hugging Face CLI, and a compatible
NVIDIA GPU/driver are required for the pinned Windows CUDA baseline. Install
and verify the ignored native/model artifacts:

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
```

Generate locally and print the result plus measurements as JSON:

```powershell
python -m runtime.inference_cli --prompt "Explain why local inference can improve privacy." --json
```

Run the tracked five-prompt baseline:

```powershell
python -m benchmarks.run_stage2_baseline --runs-per-prompt 1
```

The setup is pinned to llama.cpp `b10566` and the Q4_K_M file from
the Apache-2.0-licensed `Qwen/Qwen2.5-1.5B-Instruct-GGUF`; exact revisions and SHA-256 values live in
[`configs/inference-baseline.json`](configs/inference-baseline.json).

## Run the deterministic lifecycle

Python 3.10 or newer is required. The skeleton has no third-party runtime
dependencies.

```powershell
python -m runtime --objective "Demonstrate one local task"
```

The command prints JSON lifecycle events for:

```text
runtime.started -> task.created -> task.completed -> runtime.stopped
```

This regression path remains clearly marked `STUB (no LLM inference)` and
reports zero real LLM calls.

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

## Engineering documentation

- [Repository map](docs/repository-map.md)
- [Architecture baseline](docs/architecture.md)
- [Environment report](docs/environment.md)
- [Development commands](docs/development.md)
- [Risk register](docs/risks.md)
- [Stage 2 benchmark report](docs/benchmarks/stage2-local-inference-baseline.md)
- [Architecture decisions](docs/adr/README.md)

## Verify this machine

From PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

The script is read-only. It reports relevant local hardware and tool versions;
it does not install dependencies, start services, or download models.
