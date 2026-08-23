"""Configuration loading for the pinned llama.cpp baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class LlamaCppConfig:
    executable_path: Path
    model_path: Path
    model_id: str
    model_revision: str
    model_sha256: str | None
    executable_sha256: str | None
    release: str
    commit: str
    context_size: int
    batch_size: int
    threads: int
    gpu_layers: str | int
    flash_attention: str
    temperature: float
    seed: int
    max_generated_tokens: int
    prompt_format: str
    system_prompt: str
    resource_sample_interval_ms: int = 200
    launcher_args: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        positive = {
            "context_size": self.context_size,
            "batch_size": self.batch_size,
            "threads": self.threads,
            "max_generated_tokens": self.max_generated_tokens,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ConfigurationError(
                    f"{name} must be greater than zero",
                    details={"field": name, "value": value},
                )
        if self.resource_sample_interval_ms < 0:
            raise ConfigurationError(
                "resource_sample_interval_ms must not be negative"
            )
        if isinstance(self.gpu_layers, str):
            if self.gpu_layers not in {"all", "auto"}:
                raise ConfigurationError("gpu_layers string must be 'all' or 'auto'")
        elif not isinstance(self.gpu_layers, int) or self.gpu_layers < 0:
            raise ConfigurationError("gpu_layers must be a non-negative integer")
        if self.temperature < 0:
            raise ConfigurationError("temperature must not be negative")
        if self.flash_attention not in {"on", "off", "auto"}:
            raise ConfigurationError(
                "flash_attention must be one of: on, off, auto"
            )
        if self.prompt_format != "qwen-chatml":
            raise ConfigurationError(
                "Stage 2 supports only the pinned qwen-chatml prompt format"
            )
        if not self.model_id.strip() or not self.release.strip():
            raise ConfigurationError("model_id and release must not be empty")


def _required(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ConfigurationError(
            f"missing configuration field: {section}.{key}"
        )
    return mapping[key]


def load_llama_cpp_config(path: str | Path) -> LlamaCppConfig:
    config_path = Path(path).resolve()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "failed to read inference configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error

    if data.get("schema_version") != 1:
        raise ConfigurationError(
            "unsupported inference configuration schema",
            details={"schema_version": data.get("schema_version")},
        )

    backend = _required(data, "backend", "root")
    model = _required(data, "model", "root")
    inference = _required(data, "inference", "root")
    if not all(isinstance(section, dict) for section in (backend, model, inference)):
        raise ConfigurationError("backend, model, and inference must be objects")

    repo_root = config_path.parent.parent

    try:
        return LlamaCppConfig(
            executable_path=(repo_root / _required(backend, "executable", "backend")).resolve(),
            model_path=(repo_root / _required(model, "path", "model")).resolve(),
            model_id=str(_required(model, "id", "model")),
            model_revision=str(_required(model, "revision", "model")),
            model_sha256=str(_required(model, "sha256", "model")),
            executable_sha256=str(_required(backend, "executable_sha256", "backend")),
            release=str(_required(backend, "release", "backend")),
            commit=str(_required(backend, "commit", "backend")),
            context_size=int(_required(inference, "context_size", "inference")),
            batch_size=int(_required(inference, "batch_size", "inference")),
            threads=int(_required(inference, "threads", "inference")),
            gpu_layers=_required(inference, "gpu_layers", "inference"),
            flash_attention=str(_required(inference, "flash_attention", "inference")),
            temperature=float(_required(inference, "temperature", "inference")),
            seed=int(_required(inference, "seed", "inference")),
            max_generated_tokens=int(
                _required(inference, "max_generated_tokens", "inference")
            ),
            prompt_format=str(_required(inference, "prompt_format", "inference")),
            system_prompt=str(_required(inference, "system_prompt", "inference")),
            resource_sample_interval_ms=int(
                inference.get("resource_sample_interval_ms", 200)
            ),
        )
    except (TypeError, ValueError) as error:
        raise ConfigurationError(
            "inference configuration has an invalid field type",
            details={"cause_type": type(error).__name__},
        ) from error
