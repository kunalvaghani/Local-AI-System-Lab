"""Typed data exchanged across the Stage 1 and Stage 2 component interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from .errors import ValidationError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"


@dataclass(frozen=True, slots=True)
class Agent:
    agent_id: str
    name: str
    objective: str
    capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValidationError("agent_id must not be empty")
        if not self.name.strip():
            raise ValidationError("agent name must not be empty")
        if not self.objective.strip():
            raise ValidationError("agent objective must not be empty")


@dataclass(frozen=True, slots=True)
class Task:
    task_id: str
    agent_id: str
    objective: str
    created_at: datetime
    input_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        agent_id: str,
        objective: str,
        input_data: dict[str, Any] | None = None,
    ) -> "Task":
        return cls(
            task_id=str(uuid4()),
            agent_id=agent_id,
            objective=objective,
            created_at=utc_now(),
            input_data=dict(input_data or {}),
        )

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValidationError("task_id must not be empty")
        if not self.agent_id.strip():
            raise ValidationError("task agent_id must not be empty")
        if not self.objective.strip():
            raise ValidationError("task objective must not be empty")
        if self.created_at.tzinfo is None:
            raise ValidationError("task created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    task_id: str
    prompt: str
    model_id: str
    max_generated_tokens: int
    system_prompt: str | None = None


@dataclass(frozen=True, slots=True)
class InferenceMetrics:
    """Measured facts for one backend invocation.

    Optional fields remain ``None`` when the backend or host cannot observe a
    value. No field is estimated silently.
    """

    model_load_ms: float | None = None
    startup_to_ready_ms: float | None = None
    ttft_ms: float | None = None
    prompt_eval_ms: float | None = None
    prompt_tokens: int | None = None
    prompt_tokens_per_second: float | None = None
    generation_ms: float | None = None
    generated_token_runs: int | None = None
    tokens_per_second: float | None = None
    internal_load_ms: float | None = None
    total_ms: float | None = None
    peak_process_ram_mib: float | None = None
    baseline_vram_used_mib: float | None = None
    peak_vram_used_mib: float | None = None
    vram_delta_mib: float | None = None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }


@dataclass(frozen=True, slots=True)
class InferenceChunk:
    text: str = ""
    is_final: bool = False
    metrics: InferenceMetrics | None = None


@dataclass(frozen=True, slots=True)
class InferenceResult:
    text: str
    model_id: str
    backend_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    metrics: InferenceMetrics | None = None


@dataclass(frozen=True, slots=True)
class RouteDecision:
    model_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class Checkpoint:
    task_id: str
    phase: str
    recorded_at: datetime = field(default_factory=utc_now)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricEvent:
    name: str
    recorded_at: datetime = field(default_factory=utc_now)
    task_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskResult:
    task_id: str
    output: str
    model_id: str
    backend_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    inference_metrics: InferenceMetrics | None = None
