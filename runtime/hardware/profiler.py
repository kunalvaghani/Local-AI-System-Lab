"""Best-effort local hardware profiler with explicit evidence sources."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import sys
from time import perf_counter
from collections.abc import Callable
from typing import Any

try:
    import winreg
except ImportError:  # pragma: no cover - exercised on non-Windows hosts
    winreg = None  # type: ignore[assignment]

from .models import Confidence, CpuSnapshot, GpuSnapshot, HardwareSnapshot, RamSnapshot


NVIDIA_QUERY = (
    "name,driver_version,memory.total,memory.used,memory.free,"
    "utilization.gpu,temperature.gpu,compute_cap"
)


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class LocalHardwareProfiler:
    def __init__(
        self,
        *,
        gpu_runner: Callable[[], str] | None = None,
        memory_reader: Callable[[], tuple[int, int, str]] | None = None,
        cpu_reader: Callable[[], tuple[str | None, int | None, str]] | None = None,
    ) -> None:
        self._gpu_runner = gpu_runner or self._run_nvidia_smi
        self._memory_reader = memory_reader or self._read_memory
        self._cpu_reader = cpu_reader or self._read_cpu

    def snapshot(self) -> HardwareSnapshot:
        started = perf_counter()
        warnings: list[str] = []
        cpu_model, physical_cores, cpu_source = self._cpu_reader()
        logical = os.cpu_count() or 1
        if physical_cores is None:
            warnings.append("physical core count unavailable; logical count is not relabeled")
        cpu = CpuSnapshot(
            model=cpu_model,
            logical_processors=logical,
            physical_cores=physical_cores,
            source=cpu_source,
            confidence=Confidence.HIGH if cpu_model else Confidence.LOW,
        )
        try:
            total_bytes, available_bytes, ram_source = self._memory_reader()
            total_mib = total_bytes / (1024 * 1024)
            available_mib = available_bytes / (1024 * 1024)
            ram = RamSnapshot(
                total_mib=round(total_mib, 3),
                available_mib=round(available_mib, 3),
                used_mib=round(total_mib - available_mib, 3),
                source=ram_source,
                confidence=Confidence.HIGH,
            )
        except Exception as error:
            warnings.append(f"RAM availability unavailable: {type(error).__name__}")
            ram = RamSnapshot(None, None, None, "unavailable", Confidence.UNAVAILABLE)
        try:
            gpu = self.parse_nvidia_smi(self._gpu_runner())
        except Exception as error:
            warnings.append(f"GPU telemetry unavailable: {type(error).__name__}")
            gpu = None
        return HardwareSnapshot(
            cpu=cpu,
            ram=ram,
            gpu=gpu,
            profile_ms=round((perf_counter() - started) * 1_000, 3),
            warnings=tuple(warnings),
        )

    @staticmethod
    def parse_nvidia_smi(output: str) -> GpuSnapshot:
        row = next(line for line in output.splitlines() if line.strip())
        values = [value.strip() for value in row.split(",")]
        if len(values) != 8:
            raise ValueError("nvidia-smi returned an unexpected column count")
        return GpuSnapshot(
            name=values[0],
            driver_version=values[1],
            total_vram_mib=float(values[2]),
            used_vram_mib=float(values[3]),
            free_vram_mib=float(values[4]),
            utilization_percent=float(values[5]),
            temperature_c=float(values[6]),
            compute_capability=values[7] or None,
            source="nvidia-smi live query",
            confidence=Confidence.HIGH,
        )

    @staticmethod
    def _run_nvidia_smi() -> str:
        startupinfo: Any = None
        if sys.platform == "win32" and winreg is not None:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        completed = subprocess.run(
            [
                "nvidia-smi",
                f"--query-gpu={NVIDIA_QUERY}",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
            startupinfo=startupinfo,
        )
        return completed.stdout

    @staticmethod
    def _read_cpu() -> tuple[str | None, int | None, str]:
        if sys.platform == "win32":
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                ) as key:
                    model = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
                return model, None, "Windows registry + os.cpu_count"
            except OSError:
                pass
        model = platform.processor().strip() or None
        return model, None, "platform.processor + os.cpu_count"

    @staticmethod
    def _read_memory() -> tuple[int, int, str]:
        if sys.platform == "win32":
            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(_MemoryStatus)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                raise OSError("GlobalMemoryStatusEx failed")
            return status.ullTotalPhys, status.ullAvailPhys, "GlobalMemoryStatusEx"
        page_size = os.sysconf("SC_PAGE_SIZE")
        total_pages = os.sysconf("SC_PHYS_PAGES")
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        return (
            page_size * total_pages,
            page_size * available_pages,
            "POSIX sysconf",
        )
