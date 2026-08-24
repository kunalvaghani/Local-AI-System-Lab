"""Typed data exchanged across core component interfaces through Stage 11."""

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


class TaskState(str, Enum):
    """Inspectable Stage 4 execution and terminal failure states."""

    CREATED = "created"
    PLANNING = "planning"
    RECOVERING = "recovering"
    WAITING_FOR_TOOL = "waiting_for_tool"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    MODEL_FAILED = "model_failed"
    TOOL_FAILED = "tool_failed"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"
    OUT_OF_MEMORY = "out_of_memory"
    SECURITY_BLOCKED = "security_blocked"
    CONTEXT_OVERFLOW = "context_overflow"
    RESOURCE_BLOCKED = "resource_blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class StateTransition:
    """One validated state change in a task's ordered execution history."""

    sequence: int
    from_state: TaskState | None
    to_state: TaskState
    reason: str
    recorded_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class ToolCapabilityMetadata:
    """A narrow agent grant for one registered tool and its permissions."""

    name: str
    description: str
    permissions: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("tool capability name must not be empty")
        if not self.description.strip():
            raise ValidationError("tool capability description must not be empty")
        if any(
            not isinstance(permission, str) or not permission.strip()
            for permission in self.permissions
        ):
            raise ValidationError("tool capability permissions must not be empty")


@dataclass(frozen=True, slots=True)
class Agent:
    agent_id: str
    name: str
    objective: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    system_prompt: str = "You are a concise local assistant."
    tool_capabilities: tuple[ToolCapabilityMetadata, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.agent_id.strip():
            raise ValidationError("agent_id must not be empty")
        if not self.name.strip():
            raise ValidationError("agent name must not be empty")
        if not self.objective.strip():
            raise ValidationError("agent objective must not be empty")
        if not self.system_prompt.strip():
            raise ValidationError("agent system_prompt must not be empty")
        names = [capability.name for capability in self.tool_capabilities]
        if len(names) != len(set(names)):
            raise ValidationError("agent tool capability names must be unique")


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
    profile: "InferenceProfile | None" = None


@dataclass(frozen=True, slots=True)
class InferenceProfile:
    """One explicit, inspectable llama.cpp resource configuration."""

    profile_id: str
    purpose: str
    context_size: int
    batch_size: int
    ubatch_size: int
    threads: int
    threads_batch: int
    gpu_layers: int
    flash_attention: str
    devices: str = "auto"

    def __post_init__(self) -> None:
        positive = {
            "context_size": self.context_size,
            "batch_size": self.batch_size,
            "ubatch_size": self.ubatch_size,
            "threads": self.threads,
            "threads_batch": self.threads_batch,
        }
        if not self.profile_id.strip() or not self.purpose.strip():
            raise ValidationError("inference profile identity and purpose are required")
        for name, value in positive.items():
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValidationError(
                    f"inference profile {name} must be a positive integer",
                    details={"profile_id": self.profile_id, "value": value},
                )
        if self.ubatch_size > self.batch_size:
            raise ValidationError(
                "inference profile ubatch_size cannot exceed batch_size",
                details={"profile_id": self.profile_id},
            )
        if isinstance(self.gpu_layers, bool) or not isinstance(self.gpu_layers, int) or self.gpu_layers < 0:
            raise ValidationError("inference profile gpu_layers must be non-negative")
        if self.flash_attention not in {"on", "off", "auto"}:
            raise ValidationError(
                "inference profile flash_attention must be on, off, or auto"
            )
        if not self.devices.strip():
            raise ValidationError("inference profile devices must not be empty")

    def as_dict(self) -> dict[str, Any]:
        return {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
        }


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
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }


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
class LifecycleEvent:
    """Inspectable runtime event, separate from performance telemetry."""

    name: str
    recorded_at: datetime = field(default_factory=utc_now)
    agent_id: str | None = None
    task_id: str | None = None
    state: TaskState | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskResult:
    task_id: str
    output: str
    model_id: str
    backend_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    inference_metrics: InferenceMetrics | None = None
    agent_id: str | None = None
    objective: str | None = None
    final_state: TaskState | None = None
    state_history: tuple[StateTransition, ...] = field(default_factory=tuple)
