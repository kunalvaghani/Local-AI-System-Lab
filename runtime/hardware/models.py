"""Typed hardware evidence, memory estimates, and admission decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..errors import ValidationError
from ..models import utc_now
from ..scheduler import WorkloadClass


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNAVAILABLE = "unavailable"


class AdmissionAction(str, Enum):
    ACCEPT = "accept"
    QUEUE = "queue"
    REDUCE_CONTEXT = "reduce_context"
    REDUCE_GPU_OFFLOAD = "reduce_gpu_offload"
    FALLBACK = "fallback"
    REJECT_UNSAFE = "reject_unsafe"


@dataclass(frozen=True, slots=True)
class CpuSnapshot:
    model: str | None
    logical_processors: int
    physical_cores: int | None
    source: str
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class RamSnapshot:
    total_mib: float | None
    available_mib: float | None
    used_mib: float | None
    source: str
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class GpuSnapshot:
    name: str
    driver_version: str
    total_vram_mib: float
    used_vram_mib: float
    free_vram_mib: float
    utilization_percent: float | None
    temperature_c: float | None
    compute_capability: str | None
    source: str
    confidence: Confidence


@dataclass(frozen=True, slots=True)
class HardwareSnapshot:
    cpu: CpuSnapshot
    ram: RamSnapshot
    gpu: GpuSnapshot | None
    profile_ms: float | None = None
    captured_at: datetime = field(default_factory=utc_now)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "captured_at_utc": self.captured_at.isoformat(),
            "profile_ms": self.profile_ms,
            "cpu": {
                "model": self.cpu.model,
                "logical_processors": self.cpu.logical_processors,
                "physical_cores": self.cpu.physical_cores,
                "source": self.cpu.source,
                "confidence": self.cpu.confidence.value,
            },
            "ram": {
                "total_mib": self.ram.total_mib,
                "available_mib": self.ram.available_mib,
                "used_mib": self.ram.used_mib,
                "source": self.ram.source,
                "confidence": self.ram.confidence.value,
            },
            "gpu": (
                {
                    "name": self.gpu.name,
                    "driver_version": self.gpu.driver_version,
                    "total_vram_mib": self.gpu.total_vram_mib,
                    "used_vram_mib": self.gpu.used_vram_mib,
                    "free_vram_mib": self.gpu.free_vram_mib,
                    "utilization_percent": self.gpu.utilization_percent,
                    "temperature_c": self.gpu.temperature_c,
                    "compute_capability": self.gpu.compute_capability,
                    "source": self.gpu.source,
                    "confidence": self.gpu.confidence.value,
                }
                if self.gpu is not None
                else None
            ),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ModelMemoryProfile:
    model_id: str
    path: str
    file_size_mib: float
    quantization: str
    layer_count: int
    baseline_context_tokens: int
    baseline_gpu_layers: int

    def __post_init__(self) -> None:
        if not self.model_id.strip() or self.file_size_mib <= 0:
            raise ValidationError("model memory profile identity and size are required")
        if self.layer_count <= 0 or self.baseline_context_tokens <= 0:
            raise ValidationError("model layers and context must be positive")
        if not 0 <= self.baseline_gpu_layers <= self.layer_count:
            raise ValidationError("baseline GPU layers are outside model bounds")


@dataclass(frozen=True, slots=True)
class AdmissionRequest:
    model: ModelMemoryProfile
    context_tokens: int
    gpu_layers: int
    workload: WorkloadClass = WorkloadClass.STANDARD
    allow_context_reduction: bool = True
    allow_gpu_reduction: bool = True
    fallback_model: ModelMemoryProfile | None = None

    def __post_init__(self) -> None:
        if self.context_tokens <= 0:
            raise ValidationError("admission context_tokens must be positive")
        if not 0 <= self.gpu_layers <= self.model.layer_count:
            raise ValidationError("admission GPU layers are outside model bounds")


@dataclass(frozen=True, slots=True)
class MemoryEstimate:
    model_id: str
    context_tokens: int
    gpu_layers: int
    predicted_host_ram_mib: float
    predicted_vram_mib: float
    host_weight_component_mib: float
    host_context_component_mib: float
    host_fixed_component_mib: float
    vram_weight_component_mib: float
    vram_context_component_mib: float
    vram_fixed_component_mib: float
    confidence: Confidence
    assumptions: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "context_tokens": self.context_tokens,
            "gpu_layers": self.gpu_layers,
            "predicted_host_ram_mib": self.predicted_host_ram_mib,
            "predicted_vram_mib": self.predicted_vram_mib,
            "components": {
                "host_weight_mib": self.host_weight_component_mib,
                "host_context_mib": self.host_context_component_mib,
                "host_fixed_mib": self.host_fixed_component_mib,
                "vram_weight_mib": self.vram_weight_component_mib,
                "vram_context_mib": self.vram_context_component_mib,
                "vram_fixed_mib": self.vram_fixed_component_mib,
            },
            "confidence": self.confidence.value,
            "assumptions": list(self.assumptions),
        }


@dataclass(frozen=True, slots=True)
class CalibrationComparison:
    predicted_host_ram_mib: float
    observed_host_ram_mib: float
    host_error_mib: float
    host_error_percent: float
    predicted_vram_mib: float
    observed_vram_mib: float
    vram_error_mib: float
    vram_error_percent: float
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    action: AdmissionAction
    reason: str
    estimate: MemoryEstimate
    host_reserve_mib: float
    vram_reserve_mib: float
    available_ram_mib: float | None
    free_vram_mib: float | None
    recommended_context_tokens: int | None = None
    recommended_gpu_layers: int | None = None
    fallback_model_id: str | None = None
    confidence: Confidence = Confidence.LOW
    constraints: tuple[str, ...] = field(default_factory=tuple)

    @property
    def permitted(self) -> bool:
        return self.action is AdmissionAction.ACCEPT

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "permitted": self.permitted,
            "reason": self.reason,
            "estimate": self.estimate.as_dict(),
            "host_reserve_mib": self.host_reserve_mib,
            "vram_reserve_mib": self.vram_reserve_mib,
            "available_ram_mib": self.available_ram_mib,
            "free_vram_mib": self.free_vram_mib,
            "recommended_context_tokens": self.recommended_context_tokens,
            "recommended_gpu_layers": self.recommended_gpu_layers,
            "fallback_model_id": self.fallback_model_id,
            "confidence": self.confidence.value,
            "constraints": list(self.constraints),
        }
