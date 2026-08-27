# Setup and Reproducibility

## Supported release environment

The verified release uses Windows, Python 3.10, Node.js 24/npm 11, an NVIDIA RTX
3050 Laptop GPU, 32 GB RAM, pinned llama.cpp build 10566, and a pinned
Qwen2.5-1.5B-Instruct Q4_K_M GGUF artifact. Exact hashes and discovery sources
are recorded in the [environment report](../environment.md).

Python 3.11 is not the verified interpreter on this machine: a deliberately
faulted SQLite test can retain a Windows file handle through temporary-directory
cleanup. Use the `python` command that resolves to 3.10 for the release gate.

## Fastest deterministic setup

From the repository root:

```powershell
.\setup_and_run.bat --stub
```

The launcher checks Python/Node/npm, installs missing frontend dependencies,
starts the loopback backend first, waits for `/v1/health`, then starts Vite. It
reuses only matching healthy services and never terminates an unknown process
that owns a required port.

Open `http://127.0.0.1:4173/runtime`. Stub mode proves deterministic product
integration and reports zero real LLM calls; it is not real-inference evidence.

## Real local-model setup

Run the idempotent pinned-artifact setup when the ignored model/tools directories
are absent:

```powershell
pwsh -NoProfile -File .\scripts\setup_stage2.ps1
.\setup_and_run.bat
```

The setup verifies archive, executable, model, version, CUDA device, and SHA-256
identity. Downloads are large and require network access only during setup. The
default launcher then uses the measured direct llama.cpp backend. `--with-ollama`
starts Ollama as an optional separate service; Ollama is not the measured
flagship backend.

## Manual startup

Terminal one:

```powershell
python -m runtime.api_cli --stub --database data/portfolio-demo.db
```

Terminal two:

```powershell
cd apps/web
npm install
npm run dev
```

Both services bind to literal loopback addresses. Do not expose them to a remote
network: authentication, TLS, proxy trust, and multi-user ownership are absent.

## Verification levels

```powershell
python -m unittest discover -s tests -v
cd apps/web
npm test
npm run build
npm run check:bundle
```

The complete product release gate adds real-model, chaos/security, browser,
failure, accessibility, and restart evidence:

```powershell
python -m benchmarks.run_stage26_product_acceptance
```

Validate the portfolio release itself:

```powershell
python scripts/validate_portfolio_release.py
```

The validator checks every required document, local Markdown link, PNG identity
and dimensions, retained evidence assertion, and README release section against
the tracked [portfolio manifest](../../configs/portfolio-release.json).

## Reproducibility boundaries

- Stage 2 and Stage 26 inference numbers are hardware/model/profile-specific,
  short-run local measurements, not universal performance claims.
- GPU measurements use device-wide `nvidia-smi`; unrelated GPU activity can
  influence the result.
- The model and native binaries are ignored because of size, but their exact
  identities and setup path are tracked.
- SQLite files, security result files, screenshots from test harnesses, and local
  service logs are generated data unless explicitly copied into tracked release assets.
- Human assistive-technology testing and a clean second-machine installation are
  still required before portability or accessibility-conformance claims.
