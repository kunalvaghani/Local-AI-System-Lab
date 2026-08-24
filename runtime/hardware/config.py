"""Validated Stage 7 model metadata and estimator configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError
from .models import ModelMemoryProfile


@dataclass(frozen=True, slots=True)
class EstimatorConfig:
    host_weight_multiplier: float
    host_context_mib_per_token: float
    host_fixed_overhead_mib: float
    vram_weight_multiplier: float
    vram_context_mib_per_token: float
    vram_fixed_overhead_mib: float
    host_reserve_mib: float
    vram_reserve_mib: float
    minimum_context_tokens: int


@dataclass(frozen=True, slots=True)
class CalibrationRecord:
    source: str
    observed_peak_child_ram_mib: float
    observed_vram_delta_mib: float
    context_tokens: int
    gpu_layers: int


@dataclass(frozen=True, slots=True)
class AdmissionConfig:
    model: ModelMemoryProfile
    estimator: EstimatorConfig
    calibration: CalibrationRecord


def _number(data: dict[str, Any], name: str, section: str) -> float:
    value = data.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ConfigurationError(
            f"{section}.{name} must be a non-negative number",
            details={"value": value},
        )
    return float(value)


def load_admission_config(
    path: str | Path = "configs/admission-baseline.json",
) -> AdmissionConfig:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "could not load admission configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
    if payload.get("schema_version") != 1:
        raise ConfigurationError("unsupported admission configuration schema")

    try:
        model_data = payload["model"]
        estimator_data = payload["estimator"]
        calibration_data = payload["calibration"]
        model_path = (config_path.parent.parent / model_data["path"]).resolve()
        size_mib = model_path.stat().st_size / (1024 * 1024)
        model = ModelMemoryProfile(
            model_id=str(model_data["id"]),
            path=str(model_path),
            file_size_mib=size_mib,
            quantization=str(model_data["quantization"]),
            layer_count=int(model_data["layer_count"]),
            baseline_context_tokens=int(model_data["baseline_context_tokens"]),
            baseline_gpu_layers=int(model_data["baseline_gpu_layers"]),
        )
        estimator = EstimatorConfig(
            host_weight_multiplier=_number(estimator_data, "host_weight_multiplier", "estimator"),
            host_context_mib_per_token=_number(estimator_data, "host_context_mib_per_token", "estimator"),
            host_fixed_overhead_mib=_number(estimator_data, "host_fixed_overhead_mib", "estimator"),
            vram_weight_multiplier=_number(estimator_data, "vram_weight_multiplier", "estimator"),
            vram_context_mib_per_token=_number(estimator_data, "vram_context_mib_per_token", "estimator"),
            vram_fixed_overhead_mib=_number(estimator_data, "vram_fixed_overhead_mib", "estimator"),
            host_reserve_mib=_number(estimator_data, "host_reserve_mib", "estimator"),
            vram_reserve_mib=_number(estimator_data, "vram_reserve_mib", "estimator"),
            minimum_context_tokens=int(estimator_data["minimum_context_tokens"]),
        )
        calibration = CalibrationRecord(
            source=str(calibration_data["source"]),
            observed_peak_child_ram_mib=_number(calibration_data, "observed_peak_child_ram_mib", "calibration"),
            observed_vram_delta_mib=_number(calibration_data, "observed_vram_delta_mib", "calibration"),
            context_tokens=int(calibration_data["context_tokens"]),
            gpu_layers=int(calibration_data["gpu_layers"]),
        )
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ConfigurationError(
            "admission configuration contains invalid model metadata",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
    if estimator.minimum_context_tokens <= 0:
        raise ConfigurationError("minimum_context_tokens must be positive")
    return AdmissionConfig(model=model, estimator=estimator, calibration=calibration)
