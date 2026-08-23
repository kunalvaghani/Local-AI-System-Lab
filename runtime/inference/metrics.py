"""llama.cpp timing parsing and lightweight process resource sampling."""

from __future__ import annotations

import ctypes
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from typing import TYPE_CHECKING

from ..models import InferenceMetrics

if TYPE_CHECKING:
    from subprocess import Popen


_LOAD_RE = re.compile(r"load time\s*=\s*([\d.]+) ms")
_PROMPT_RE = re.compile(
    r"prompt eval time\s*=\s*([\d.]+) ms\s*/\s*(\d+) tokens.*?"
    r"([\d.]+) tokens per second"
)
_EVAL_RE = re.compile(
    r"(?<!prompt )eval time\s*=\s*([\d.]+) ms\s*/\s*(\d+) runs.*?"
    r"([\d.]+) tokens per second"
)
_CLOCK_RE = re.compile(r"^(\d+)\.(\d{2})\.(\d{3})\.(\d{3})")


def _match_float(pattern: re.Pattern[str], text: str, group: int) -> float | None:
    match = pattern.search(text)
    return float(match.group(group)) if match else None


def _match_int(pattern: re.Pattern[str], text: str, group: int) -> int | None:
    match = pattern.search(text)
    return int(match.group(group)) if match else None


def _log_clock_ms(line: str) -> float | None:
    match = _CLOCK_RE.match(line)
    if not match:
        return None
    minutes, seconds, milliseconds, microseconds = map(int, match.groups())
    return (
        minutes * 60_000.0
        + seconds * 1_000.0
        + milliseconds
        + microseconds / 1_000.0
    )


def _model_load_ms(stderr_text: str) -> float | None:
    start: float | None = None
    for line in stderr_text.splitlines():
        timestamp = _log_clock_ms(line)
        if timestamp is None:
            continue
        if "load the model and apply" in line:
            start = timestamp
        elif start is not None and "llama threadpool init" in line:
            return max(0.0, timestamp - start)
    return None


def parse_llama_metrics(
    stderr_text: str,
    *,
    startup_to_ready_ms: float | None,
    ttft_ms: float | None,
    total_ms: float,
    peak_process_ram_mib: float | None,
    baseline_vram_used_mib: float | None,
    peak_vram_used_mib: float | None,
) -> InferenceMetrics:
    vram_delta: float | None = None
    if baseline_vram_used_mib is not None and peak_vram_used_mib is not None:
        vram_delta = max(0.0, peak_vram_used_mib - baseline_vram_used_mib)

    return InferenceMetrics(
        model_load_ms=_model_load_ms(stderr_text),
        startup_to_ready_ms=startup_to_ready_ms,
        ttft_ms=ttft_ms,
        prompt_eval_ms=_match_float(_PROMPT_RE, stderr_text, 1),
        prompt_tokens=_match_int(_PROMPT_RE, stderr_text, 2),
        prompt_tokens_per_second=_match_float(_PROMPT_RE, stderr_text, 3),
        generation_ms=_match_float(_EVAL_RE, stderr_text, 1),
        generated_token_runs=_match_int(_EVAL_RE, stderr_text, 2),
        tokens_per_second=_match_float(_EVAL_RE, stderr_text, 3),
        internal_load_ms=_match_float(_LOAD_RE, stderr_text, 1),
        total_ms=total_ms,
        peak_process_ram_mib=peak_process_ram_mib,
        baseline_vram_used_mib=baseline_vram_used_mib,
        peak_vram_used_mib=peak_vram_used_mib,
        vram_delta_mib=vram_delta,
    )


def _no_window_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def query_total_vram_used_mib() -> float | None:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=_no_window_flags(),
        )
        if completed.returncode != 0:
            return None
        values = [float(line.strip()) for line in completed.stdout.splitlines()]
        return sum(values) if values else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _process_peak_ram_mib(process: "Popen[bytes]") -> float | None:
    if os.name == "nt":
        try:
            class ProcessMemoryCounters(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.c_void_p(int(process._handle))  # type: ignore[attr-defined]
            success = ctypes.windll.psapi.GetProcessMemoryInfo(  # type: ignore[attr-defined]
                handle,
                ctypes.byref(counters),
                counters.cb,
            )
            if success:
                return counters.PeakWorkingSetSize / (1024.0 * 1024.0)
        except (AttributeError, OSError, TypeError, ValueError):
            return None
    else:
        try:
            status = Path(f"/proc/{process.pid}/status").read_text(encoding="utf-8")
            match = re.search(r"^VmHWM:\s+(\d+)\s+kB$", status, re.MULTILINE)
            if match:
                return int(match.group(1)) / 1024.0
        except OSError:
            return None
    return None


@dataclass(slots=True)
class ResourceSnapshot:
    peak_process_ram_mib: float | None
    baseline_vram_used_mib: float | None
    peak_vram_used_mib: float | None


class ProcessResourceSampler:
    """Coarse sampler; GPU polling overhead is documented in benchmark output."""

    def __init__(
        self,
        process: "Popen[bytes]",
        interval_ms: int,
        *,
        baseline_vram_used_mib: float | None = None,
    ) -> None:
        self._process = process
        self._interval_seconds = interval_ms / 1000.0
        self._stop = Event()
        self._thread: Thread | None = None
        self._peak_ram: float | None = None
        self._baseline_vram = baseline_vram_used_mib
        self._peak_vram = self._baseline_vram

    def start(self) -> None:
        if self._interval_seconds <= 0:
            return
        self._thread = Thread(target=self._run, name="resource-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> ResourceSnapshot:
        self._sample()
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self._interval_seconds * 2))
        return ResourceSnapshot(
            peak_process_ram_mib=self._peak_ram,
            baseline_vram_used_mib=self._baseline_vram,
            peak_vram_used_mib=self._peak_vram,
        )

    def _run(self) -> None:
        while not self._stop.wait(self._interval_seconds):
            self._sample()
            if self._process.poll() is not None:
                return

    def _sample(self) -> None:
        ram = _process_peak_ram_mib(self._process)
        if ram is not None and (self._peak_ram is None or ram > self._peak_ram):
            self._peak_ram = ram
        if self._interval_seconds <= 0:
            return
        vram = query_total_vram_used_mib()
        if vram is not None and (
            self._peak_vram is None or vram > self._peak_vram
        ):
            self._peak_vram = vram
