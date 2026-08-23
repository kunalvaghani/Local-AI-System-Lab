# Development and Verification Commands

## Current setup

The Python package supports Python 3.10 or newer and has no third-party runtime
or test dependencies. Stage 2 additionally uses pinned, ignored native binaries
and a GGUF model. `pyproject.toml` and `configs/inference-baseline.json` are the
tracked package/inference sources of truth.

Clone and inspect:

```powershell
git clone https://github.com/kunalvaghani/Local-AI-System-Lab.git
Set-Location Local-AI-System-Lab
git status --short --branch
```

Collect the environment baseline:

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

Run the lifecycle demonstration:

```powershell
python -m runtime --objective "Demonstrate one local task"
```

Install or verify the pinned Stage 2 artifacts (network is used only when an
artifact is absent):

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
```

Run real local inference:

```powershell
python -m runtime.inference_cli --prompt "Explain local inference in one sentence." --json
```

Exercise owned-process cancellation:

```powershell
python -m runtime.inference_cli --prompt "Write a long explanation." --max-tokens 64 --cancel-after-ms 1800
```

Run and record a new five-prompt cold baseline:

```powershell
python -m benchmarks.run_stage2_baseline --runs-per-prompt 1
```

Run the standard-library test suite:

```powershell
python -m unittest discover -s tests -v
```

Validate Python syntax without executing application code:

```powershell
python -m compileall -q runtime tests benchmarks
```

Validate package metadata without installing the project or dependencies:

```powershell
python -m pip install --dry-run --no-deps --no-build-isolation .
```

Inspect tracked project files without descending into `.git`:

```powershell
rg --files -uu -g '!.git/**'
```

Check unfinished-work markers:

```powershell
rg -n -uu -g '!.git/**' 'TODO|FIXME|HACK|XXX' .
```

Review local changes:

```powershell
git status --short
git diff --check
git diff
```

## Commands intentionally undefined

There is no database migration, API server, or frontend command because those
capabilities do not exist yet. Formatting,
linting, type-checking, and coverage tools are not declared until their cost and
configuration are selected in a later approved stage.

## Development discipline

1. Read `PROJECT_STATE.md` and the relevant architecture/ADR documents.
2. Confirm the explicitly approved stage and its stopping point.
3. Inspect status, source, tests, configs, and TODO markers before editing.
4. Make the smallest implementation that produces the stage's new capability.
5. Run real tests and record exact commands/results.
6. Update `PROJECT_STATE.md` to evidence, then stop for approval.

Performance work follows:

```text
BASELINE -> PROFILE -> HYPOTHESIS -> CHANGE -> BENCHMARK -> KEEP/REVERT
```
