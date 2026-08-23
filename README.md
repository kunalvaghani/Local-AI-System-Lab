# Local AI Systems Lab

A stage-gated portfolio project for building an inspectable local AI runtime on
constrained consumer hardware. The current skeleton composes typed runtime
interfaces through deterministic, in-memory implementations. It does not yet
perform real LLM inference.

## Current status

- Last completed stage: Stage 1 — Project Skeleton & Core Interfaces
- Next approval-gated stage: Stage 2 — Local Inference Baseline
- Backend acceptance: NOT STARTED
- Frontend work: PROHIBITED until the backend acceptance gate passes

See [PROJECT_STATE.md](PROJECT_STATE.md) for the source-of-truth status.

## Run the Stage 1 lifecycle

Python 3.10 or newer is required. The skeleton has no third-party runtime
dependencies.

```powershell
python -m runtime --objective "Demonstrate one local task"
```

The command prints JSON lifecycle events for:

```text
runtime.started -> task.created -> task.completed -> runtime.stopped
```

The output is clearly marked `STUB (no LLM inference)` and reports zero real
LLM calls.

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
- [Architecture decisions](docs/adr/README.md)

## Verify this machine

From PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

The script is read-only. It reports relevant local hardware and tool versions;
it does not install dependencies, start services, or download models.
