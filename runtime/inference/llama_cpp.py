"""Pinned llama.cpp subprocess backend with streaming and measured metrics."""

from __future__ import annotations

import codecs
import hashlib
import os
import queue
import re
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from threading import Lock, Thread
from typing import BinaryIO

from ..cancellation import CancellationToken
from ..errors import (
    ComponentOperationError,
    ContextOverflowError,
    InferenceCancelledError,
    ModelOutOfMemoryError,
    RuntimeLifecycleError,
    ValidationError,
)
from ..models import (
    InferenceChunk,
    InferenceRequest,
    InferenceResult,
)
from .config import LlamaCppConfig
from .metrics import (
    ProcessResourceSampler,
    parse_llama_metrics,
    query_total_vram_used_mib,
)


_END_MARKER_RE = re.compile(r"\s*\[end of text\]\s*$", re.IGNORECASE)
_TAIL_HOLDBACK = 24


def _no_window_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _render_qwen_chatml(system_prompt: str, user_prompt: str) -> str:
    return (
        "<|im_start|>system\n"
        f"{system_prompt}<|im_end|>\n"
        "<|im_start|>user\n"
        f"{user_prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


def _read_stdout(
    stream: BinaryIO,
    events: "queue.Queue[tuple[str, str]]",
) -> None:
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    try:
        while True:
            data = os.read(stream.fileno(), 8)
            if not data:
                break
            text = decoder.decode(data)
            if text:
                events.put(("stdout", text))
        remainder = decoder.decode(b"", final=True)
        if remainder:
            events.put(("stdout", remainder))
    finally:
        events.put(("stdout_done", ""))


def _read_stderr(
    stream: BinaryIO,
    events: "queue.Queue[tuple[str, str]]",
) -> None:
    try:
        while True:
            line = stream.readline()
            if not line:
                break
            events.put(("stderr", line.decode("utf-8", errors="replace")))
    finally:
        events.put(("stderr_done", ""))


def _terminate(process: "subprocess.Popen[bytes]") -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def _native_failure(exit_code: int, stderr_text: str) -> ComponentOperationError:
    details = {
        "exit_code": exit_code,
        "stderr_tail": "\n".join(stderr_text.splitlines()[-12:]).strip(),
    }
    normalized = stderr_text.lower()
    if any(
        marker in normalized
        for marker in (
            "out of memory",
            "cuda_error_out_of_memory",
            "failed to allocate",
        )
    ):
        return ModelOutOfMemoryError(
            "llama.cpp could not allocate model memory",
            details=details,
        )
    if "context" in normalized and any(
        marker in normalized
        for marker in ("overflow", "exceeds", "too long", "too large")
    ):
        return ContextOverflowError(
            "llama.cpp rejected the request context",
            details=details,
        )
    return ComponentOperationError(
        "llama.cpp inference failed",
        details=details,
    )
class LlamaCppCompletionBackend:
    """Runs one pinned ``llama-completion`` process per inference request."""

    def __init__(self, config: LlamaCppConfig) -> None:
        self._config = config
        self._started = False
        self._version = "UNKNOWN"
        self._active_process: subprocess.Popen[bytes] | None = None
        self._process_lock = Lock()
        self._execution_lock = Lock()

    @property
    def name(self) -> str:
        return "llama.cpp-completion"

    @property
    def version(self) -> str:
        return self._version

    def start(self) -> None:
        if self._started:
            raise RuntimeLifecycleError("llama.cpp backend is already started")
        self._validate_artifact(
            self._config.executable_path,
            self._config.executable_sha256,
            "llama.cpp executable",
        )
        self._validate_artifact(
            self._config.model_path,
            self._config.model_sha256,
            "GGUF model",
        )
        try:
            completed = subprocess.run(
                [
                    str(self._config.executable_path),
                    *self._config.launcher_args,
                    "--version",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self._config.executable_path.parent,
                creationflags=_no_window_flags(),
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ComponentOperationError(
                "failed to execute llama.cpp version check",
                details={"cause_type": type(error).__name__},
            ) from error
        if completed.returncode != 0:
            raise ComponentOperationError(
                "llama.cpp version check failed",
                details={"exit_code": completed.returncode},
            )
        self._version = (completed.stdout or completed.stderr).strip()
        self._started = True

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        parts: list[str] = []
        final_metrics = None
        for chunk in self.stream(request, cancellation):
            if chunk.text:
                parts.append(chunk.text)
            if chunk.is_final:
                final_metrics = chunk.metrics
        return InferenceResult(
            text="".join(parts),
            model_id=self._config.model_id,
            backend_name=self.name,
            metadata={
                "real_llm_calls": 1,
                "mode": "local-gguf",
                "llama_cpp_release": self._config.release,
                "llama_cpp_commit": self._config.commit,
                "model_revision": self._config.model_revision,
                "inference_profile": (
                    request.profile.as_dict() if request.profile is not None else None
                ),
            },
            metrics=final_metrics,
        )

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> Iterator[InferenceChunk]:
        if not self._started:
            raise RuntimeLifecycleError("llama.cpp backend must be started first")
        if not request.prompt.strip():
            raise ValidationError("inference prompt must not be empty")
        if request.max_generated_tokens <= 0:
            raise ValidationError("max_generated_tokens must be greater than zero")

        token = cancellation or CancellationToken()
        if token.is_cancelled:
            raise InferenceCancelledError(
                "inference was cancelled before launch",
                details={"task_id": request.task_id},
            )
        if not self._execution_lock.acquire(blocking=False):
            raise ComponentOperationError(
                "this backend allows only one active inference process"
            )

        command = self._build_command(request)
        baseline_vram = (
            query_total_vram_used_mib()
            if self._config.resource_sample_interval_ms > 0
            else None
        )
        started_at = time.perf_counter()
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self._config.executable_path.parent,
                creationflags=_no_window_flags(),
            )
        except OSError as error:
            self._execution_lock.release()
            raise ComponentOperationError(
                "failed to launch llama.cpp inference",
                details={"cause_type": type(error).__name__},
            ) from error

        with self._process_lock:
            if self._active_process is not None:
                _terminate(process)
                self._execution_lock.release()
                raise ComponentOperationError(
                    "this backend allows only one active inference process"
                )
            self._active_process = process

        if process.stdout is None or process.stderr is None:
            _terminate(process)
            with self._process_lock:
                if self._active_process is process:
                    self._active_process = None
            self._execution_lock.release()
            raise ComponentOperationError("failed to open llama.cpp output pipes")

        sampler = ProcessResourceSampler(
            process,
            self._config.resource_sample_interval_ms,
            baseline_vram_used_mib=baseline_vram,
        )
        sampler.start()
        events: "queue.Queue[tuple[str, str]]" = queue.Queue()
        stdout_thread = Thread(
            target=_read_stdout,
            args=(process.stdout, events),
            name="llama-stdout",
            daemon=True,
        )
        stderr_thread = Thread(
            target=_read_stderr,
            args=(process.stderr, events),
            name="llama-stderr",
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        stderr_lines: list[str] = []
        stdout_done = False
        stderr_done = False
        tail = ""
        ttft_ms: float | None = None
        startup_to_ready_ms: float | None = None
        cancelled = False
        snapshot = None

        try:
            while not (stdout_done and stderr_done and process.poll() is not None):
                if token.is_cancelled and not cancelled:
                    cancelled = True
                    _terminate(process)
                try:
                    kind, value = events.get(timeout=0.05)
                except queue.Empty:
                    continue

                elapsed_ms = (time.perf_counter() - started_at) * 1_000.0
                if kind == "stdout":
                    if ttft_ms is None and value:
                        ttft_ms = elapsed_ms
                    tail += value
                    if len(tail) > _TAIL_HOLDBACK:
                        emit_count = len(tail) - _TAIL_HOLDBACK
                        emitted, tail = tail[:emit_count], tail[emit_count:]
                        if emitted:
                            yield InferenceChunk(text=emitted)
                elif kind == "stderr":
                    stderr_lines.append(value)
                    if startup_to_ready_ms is None and "generate: n_ctx" in value:
                        startup_to_ready_ms = elapsed_ms
                elif kind == "stdout_done":
                    stdout_done = True
                elif kind == "stderr_done":
                    stderr_done = True

            exit_code = process.wait(timeout=5)
            snapshot = sampler.stop()
            total_ms = (time.perf_counter() - started_at) * 1_000.0

            if cancelled:
                raise InferenceCancelledError(
                    "llama.cpp inference was cancelled",
                    details={"task_id": request.task_id},
                )
            if exit_code != 0:
                raise _native_failure(exit_code, "".join(stderr_lines))

            cleaned_tail = _END_MARKER_RE.sub("", tail).rstrip()
            if cleaned_tail:
                yield InferenceChunk(text=cleaned_tail)

            metrics = parse_llama_metrics(
                "".join(stderr_lines),
                startup_to_ready_ms=startup_to_ready_ms,
                ttft_ms=ttft_ms,
                total_ms=total_ms,
                peak_process_ram_mib=snapshot.peak_process_ram_mib,
                baseline_vram_used_mib=snapshot.baseline_vram_used_mib,
                peak_vram_used_mib=snapshot.peak_vram_used_mib,
            )
            yield InferenceChunk(is_final=True, metrics=metrics)
        finally:
            if process.poll() is None:
                _terminate(process)
            if snapshot is None:
                sampler.stop()
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            process.stdout.close()
            process.stderr.close()
            with self._process_lock:
                if self._active_process is process:
                    self._active_process = None
            self._execution_lock.release()

    def shutdown(self) -> None:
        with self._process_lock:
            active = self._active_process
        if active is not None:
            _terminate(active)
        self._started = False

    def _build_command(self, request: InferenceRequest) -> list[str]:
        prompt = _render_qwen_chatml(
            request.system_prompt or self._config.system_prompt,
            request.prompt,
        )
        token_limit = min(
            request.max_generated_tokens,
            self._config.max_generated_tokens,
        )
        profile = request.profile
        context_size = profile.context_size if profile else self._config.context_size
        batch_size = profile.batch_size if profile else self._config.batch_size
        threads = profile.threads if profile else self._config.threads
        gpu_layers = profile.gpu_layers if profile else self._config.gpu_layers
        flash_attention = (
            profile.flash_attention if profile else self._config.flash_attention
        )
        command = [
            str(self._config.executable_path),
            *self._config.launcher_args,
            "--model",
            str(self._config.model_path),
            "--prompt",
            prompt,
            "--predict",
            str(token_limit),
            "--ctx-size",
            str(context_size),
            "--batch-size",
            str(batch_size),
            "--threads",
            str(threads),
            "--gpu-layers",
            str(gpu_layers),
            "--flash-attn",
            flash_attention,
            "--temperature",
            str(self._config.temperature),
            "--seed",
            str(self._config.seed),
            "--fit",
            "off",
            "--no-conversation",
            "--no-display-prompt",
            "--simple-io",
            "--no-warmup",
            "--offline",
            "--perf",
            "--log-colors",
            "off",
            "--verbosity",
            "3",
        ]
        if profile is not None:
            command.extend(
                [
                    "--device",
                    profile.devices,
                    "--ubatch-size",
                    str(profile.ubatch_size),
                    "--threads-batch",
                    str(profile.threads_batch),
                ]
            )
        return command

    @staticmethod
    def _validate_artifact(
        path: Path,
        expected_sha256: str | None,
        label: str,
    ) -> None:
        if not path.is_file():
            raise ComponentOperationError(
                f"{label} was not found",
                details={"path": str(path)},
            )
        if expected_sha256 is None:
            return
        actual = _sha256(path)
        if actual.lower() != expected_sha256.lower():
            raise ComponentOperationError(
                f"{label} SHA-256 verification failed",
                details={
                    "path": str(path),
                    "expected": expected_sha256.lower(),
                    "actual": actual.lower(),
                },
            )
