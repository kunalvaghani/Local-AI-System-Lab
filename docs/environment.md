# Hardware and Software Environment Baseline

Captured on 2026-08-23 at approximately 22:49 Asia/Calcutta. Values marked
`observed` came from commands executed during Stage 0; values marked `declared`
come from the project constraints. Transient free-memory values are snapshots,
not capacity guarantees.

## Hardware

| Item | Evidence | Value |
| --- | --- | --- |
| CPU model | observed, registry | AMD Ryzen 7 5800H with Radeon Graphics |
| CPU topology | declared + observed | 8 physical cores (declared), 16 logical processors (observed) |
| Physical RAM | declared + observed | 32 GB declared; 33,656,832,000 bytes / 31.34 GiB observed |
| GPU | observed, `nvidia-smi` | NVIDIA GeForce RTX 3050 Laptop GPU |
| GPU compute capability | observed | 8.6 |
| VRAM | observed | 4,096 MiB total; 3,962 MiB free at capture |
| GPU driver | observed | 610.74 |
| GPU snapshot | observed | 0% utilization, 53 C, 15.03 W at capture |

The 134 MiB difference between total and reported free VRAM while usage was
reported as 0 MiB is retained as tool-reported evidence; no workload conclusion
is drawn from it.

## Operating system and tools

| Tool/system | Observed value | Status for future work |
| --- | --- | --- |
| Windows kernel | Microsoft Windows NT 10.0.26200.0 | Available |
| Registry product data | ProductName `Windows 10 Home Single Language`, DisplayVersion `25H2`, build `26200.9168` | Raw evidence; marketing name not inferred |
| PowerShell | 7.6.4 | Available |
| Git | 2.49.1.windows.1 | Available |
| Python (`python`) | 3.10.6 | Available; candidate baseline interpreter |
| Python launcher (`py`) | 3.11.9 | Available; version mismatch must be handled explicitly |
| pip | 26.1.2 for Python 3.10 | Available |
| pytest | Not installed for Python 3.10 | Not required; Stage 1 uses standard-library `unittest` |
| CMake | 4.1.0 | Available; not currently required |
| Node.js | 24.14.0 | Available; frontend use deferred |
| npm | 11.11.1 | Available; frontend use deferred |
| .NET SDK | 9.0.302 | Available; not currently required |
| Ollama | Client 0.32.14; service unreachable during inspection | Not used for the Stage 2 baseline |
| Hugging Face CLI | huggingface_hub 0.36.0 | Available for later model discovery/download |
| llama.cpp | Local ignored Windows CUDA artifacts, build 10566 / commit `bb4caa754` | Verified Stage 2 backend; intentionally not placed on global `PATH` |
| CUDA compiler (`nvcc`) | Not found on `PATH` | May be unnecessary if using compatible prebuilt llama.cpp binaries |
| Rust/uv | Not found on `PATH` | Not current prerequisites |
| Firecrawl CLI | Not found on `PATH` | Plugin search was used for Stage 2 official-source discovery |

## Stage 2 local artifacts

Captured on 2026-08-23. These large/generated files are ignored by Git and can
be reproduced with `scripts/setup_stage2.ps1`.

| Artifact | Pinned identity | Verified SHA-256 |
| --- | --- | --- |
| llama.cpp Windows CUDA 12.4 archive | release `b10566`, 250,963,000 bytes | `6805bde00c16006cdcc757a132f7ba95d82b5f1e6ddba7e1d91f80c4e6930dcb` |
| CUDA runtime archive | release `b10566`, 391,443,627 bytes | `8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6` |
| `llama-completion.exe` | build 10566 / commit `bb4caa754` | `de3a1b707adb9d0b9241d93e1fe6547e108e978b64d350ae4c465ad5c6e5775f` |
| Qwen2.5 1.5B Instruct Q4_K_M GGUF | revision `91cad51170dc346986eccefdc2dd33a9da36ead9`, 1,117,320,736 bytes | `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` |

At backend launch, CUDA reported the RTX 3050 with 4,095 MiB capacity and
approximately 3,305 MiB free after CUDA initialization. The Stage 2 benchmark
observed a 1,219 MiB device VRAM delta and about 1,339 MiB peak child-process
working set.

## Inspection limitations

- Broad `Get-CimInstance` and `systeminfo` calls were denied in the current execution context.
- Narrow registry reads, .NET memory APIs, environment APIs, and `nvidia-smi` succeeded.
- Stage 2 measures short cold-process inference only; it does not claim sustained clocks or thermal behavior.
- Model caches outside the repository were not inventoried because Stage 0 does not select or download a model.

## Reproduce

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

The script reports current values and labels missing optional commands without
failing solely because later-stage tools are absent.
