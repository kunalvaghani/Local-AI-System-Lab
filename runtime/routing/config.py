"""Validated Stage 9 model-registry and budget-policy loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError
from ..scheduler import WorkloadClass
from .models import (
    ComputeBudget,
    HistoricalBenchmark,
    LatencyClass,
    RegisteredModel,
)


@dataclass(frozen=True, slots=True)
class ModelRegistry:
    models: tuple[RegisteredModel, ...]
    notes: tuple[str, ...]

    def get(self, model_id: str) -> RegisteredModel:
        for model in self.models:
            if model.model_id == model_id:
                return model
        raise ConfigurationError("model is not registered", details={"model_id": model_id})

    @property
    def available_models(self) -> tuple[RegisteredModel, ...]:
        return tuple(model for model in self.models if model.available)


@dataclass(frozen=True, slots=True)
class ComputeBudgetPolicy:
    workload_budgets: dict[WorkloadClass, ComputeBudget]

    def resolve(
        self,
        workload: WorkloadClass,
        override: ComputeBudget | None = None,
    ) -> ComputeBudget:
        return override or self.workload_budgets[workload]


def _budget(payload: dict[str, Any]) -> ComputeBudget:
    return ComputeBudget(
        max_inference_calls=int(payload["max_inference_calls"]),
        max_generated_tokens=int(payload["max_generated_tokens"]),
        total_time_ms=int(payload["total_time_ms"]),
        max_ram_mib=(float(payload["max_ram_mib"]) if payload.get("max_ram_mib") is not None else None),
        max_vram_mib=(float(payload["max_vram_mib"]) if payload.get("max_vram_mib") is not None else None),
    )


def load_model_registry(
    path: str | Path = "configs/model-registry.json",
) -> tuple[ModelRegistry, ComputeBudgetPolicy]:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ConfigurationError("unsupported model-registry schema")
        repo_root = config_path.parent.parent
        models: list[RegisteredModel] = []
        for item in payload["models"]:
            benchmark_payload = item.get("historical_benchmark")
            benchmark = (
                HistoricalBenchmark(
                    source=str(benchmark_payload["source"]),
                    profile_id=str(benchmark_payload["profile_id"]),
                    ttft_ms=float(benchmark_payload["ttft_ms"]),
                    tokens_per_second=float(benchmark_payload["tokens_per_second"]),
                    measured_at_utc=str(benchmark_payload["measured_at_utc"]),
                    confidence=str(benchmark_payload.get("confidence", "measured")),
                )
                if benchmark_payload is not None
                else None
            )
            models.append(
                RegisteredModel(
                    model_id=str(item["id"]),
                    display_name=str(item["display_name"]),
                    purpose=str(item["purpose"]),
                    path=(repo_root / str(item["path"])).resolve(),
                    quantization=str(item["quantization"]),
                    parameter_count_billions=float(item["parameter_count_billions"]),
                    capabilities=frozenset(str(value) for value in item["capabilities"]),
                    max_context_tokens=int(item["max_context_tokens"]),
                    max_output_tokens=int(item["max_output_tokens"]),
                    latency_class=LatencyClass(str(item["latency_class"])),
                    quality_rank=int(item["quality_rank"]),
                    minimum_ram_mib=float(item["minimum_ram_mib"]),
                    minimum_vram_mib=float(item["minimum_vram_mib"]),
                    backend_configured=bool(item["backend_configured"]),
                    benchmark=benchmark,
                )
            )
        ids = [model.model_id for model in models]
        if not models or len(ids) != len(set(ids)):
            raise ConfigurationError("model registry IDs must be non-empty and unique")
        budgets = {
            workload: _budget(payload["compute_budgets"][workload.value])
            for workload in WorkloadClass
        }
        return (
            ModelRegistry(tuple(models), tuple(str(note) for note in payload.get("notes", []))),
            ComputeBudgetPolicy(budgets),
        )
    except ConfigurationError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "could not load model-registry configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
