"""Typed model-registry, routing, and compute-budget evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ..errors import ValidationError
from ..hardware import HardwareSnapshot
from ..scheduler import SchedulingOptions, WorkloadClass


class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LatencyClass(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    THROUGHPUT = "throughput"


@dataclass(frozen=True, slots=True)
class HistoricalBenchmark:
    source: str
    profile_id: str
    ttft_ms: float
    tokens_per_second: float
    measured_at_utc: str
    confidence: str = "measured"

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.profile_id.strip():
            raise ValidationError("benchmark source and profile are required")
        if self.ttft_ms <= 0 or self.tokens_per_second <= 0:
            raise ValidationError("benchmark latency and throughput must be positive")

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class RegisteredModel:
    model_id: str
    display_name: str
    purpose: str
    path: Path
    quantization: str
    parameter_count_billions: float
    capabilities: frozenset[str]
    max_context_tokens: int
    max_output_tokens: int
    latency_class: LatencyClass
    quality_rank: int
    minimum_ram_mib: float
    minimum_vram_mib: float
    backend_configured: bool
    benchmark: HistoricalBenchmark | None = None

    def __post_init__(self) -> None:
        if not all((self.model_id.strip(), self.display_name.strip(), self.purpose.strip())):
            raise ValidationError("registered model identity and purpose are required")
        if not self.capabilities or any(not value.strip() for value in self.capabilities):
            raise ValidationError("registered model capabilities must not be empty")
        if self.parameter_count_billions <= 0:
            raise ValidationError("registered model parameter count must be positive")
        if self.max_context_tokens <= 0 or self.max_output_tokens <= 0:
            raise ValidationError("registered model token limits must be positive")
        if not 1 <= self.quality_rank <= 10:
            raise ValidationError("registered model quality_rank must be between 1 and 10")
        if self.minimum_ram_mib <= 0 or self.minimum_vram_mib < 0:
            raise ValidationError("registered model minimum memory is invalid")

    @property
    def artifact_available(self) -> bool:
        return self.path.is_file()

    @property
    def available(self) -> bool:
        return self.artifact_available and self.backend_configured

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "purpose": self.purpose,
            "path": str(self.path),
            "artifact_available": self.artifact_available,
            "backend_configured": self.backend_configured,
            "available": self.available,
            "quantization": self.quantization,
            "parameter_count_billions": self.parameter_count_billions,
            "capabilities": sorted(self.capabilities),
            "max_context_tokens": self.max_context_tokens,
            "max_output_tokens": self.max_output_tokens,
            "latency_class": self.latency_class.value,
            "quality_rank": self.quality_rank,
            "minimum_ram_mib": self.minimum_ram_mib,
            "minimum_vram_mib": self.minimum_vram_mib,
            "benchmark": self.benchmark.as_dict() if self.benchmark else None,
        }


@dataclass(frozen=True, slots=True)
class ComputeBudget:
    max_inference_calls: int
    max_generated_tokens: int
    total_time_ms: int
    max_ram_mib: float | None
    max_vram_mib: float | None

    def __post_init__(self) -> None:
        if isinstance(self.max_inference_calls, bool) or self.max_inference_calls < 0:
            raise ValidationError("budget max_inference_calls must be non-negative")
        if self.max_generated_tokens <= 0 or self.total_time_ms <= 0:
            raise ValidationError("budget token and time limits must be positive")
        for name, value in (("max_ram_mib", self.max_ram_mib), ("max_vram_mib", self.max_vram_mib)):
            if value is not None and value < 0:
                raise ValidationError(f"budget {name} must be non-negative when set")

    def as_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class RoutingContext:
    scheduling: SchedulingOptions
    budget: ComputeBudget
    queue_depth: int
    hardware: HardwareSnapshot


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    model_id: str
    accepted: bool
    score: float | None
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "accepted": self.accepted,
            "score": self.score,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class BudgetUsage:
    inference_calls: int
    generated_tokens: int | None
    elapsed_ms: float
    peak_ram_mib: float | None
    vram_delta_mib: float | None
    preflight_enforced: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "inference_calls": self.inference_calls,
            "generated_tokens": self.generated_tokens,
            "elapsed_ms": self.elapsed_ms,
            "peak_ram_mib": self.peak_ram_mib,
            "vram_delta_mib": self.vram_delta_mib,
            "preflight_enforced": list(self.preflight_enforced),
        }
