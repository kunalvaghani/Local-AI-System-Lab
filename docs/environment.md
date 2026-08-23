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
| Ollama | Client 0.32.14; service unreachable | Optional prototype path only |
| Hugging Face CLI | huggingface_hub 0.36.0 | Available for later model discovery/download |
| llama.cpp CLI | Not found on `PATH` | Required for serious inference work in Stage 2 or later |
| CUDA compiler (`nvcc`) | Not found on `PATH` | May be unnecessary if using compatible prebuilt llama.cpp binaries |
| Rust/uv | Not found on `PATH` | Not current prerequisites |
| Firecrawl CLI | Not found on `PATH` | Plugin/app may be used when a research stage requires it; not needed in Stage 0 |

## Inspection limitations

- Broad `Get-CimInstance` and `systeminfo` calls were denied in the current execution context.
- Narrow registry reads, .NET memory APIs, environment APIs, and `nvidia-smi` succeeded.
- This baseline does not claim sustained clocks, thermals, inference throughput, or usable VRAM under load.
- Model caches outside the repository were not inventoried because Stage 0 does not select or download a model.

## Reproduce

```powershell
pwsh -NoProfile -File .\scripts\check_environment.ps1
```

The script reports current values and labels missing optional commands without
failing solely because later-stage tools are absent.
