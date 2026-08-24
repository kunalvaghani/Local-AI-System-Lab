"""Typed scheduler options, request state, results, and queue metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum

from ..cancellation import CancellationToken
from ..errors import ValidationError
from ..models import InferenceResult


class SchedulerPolicy(str, Enum):
    FIFO = "fifo"
    PRIORITY = "priority"


class WorkloadClass(str, Enum):
    INTERACTIVE = "interactive"
    STANDARD = "standard"
    BACKGROUND = "background"


class RequestPriority(IntEnum):
    BACKGROUND = 10
    STANDARD = 50
    INTERACTIVE = 100


class SchedulerRequestStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SchedulingOptions:
    workload: WorkloadClass = WorkloadClass.STANDARD
    priority: int | None = None
    timeout_ms: int | None = 30_000
    cancellation: CancellationToken | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.workload, WorkloadClass):
            raise ValidationError(
                "scheduler workload must be a WorkloadClass",
                details={"actual_type": type(self.workload).__name__},
            )
        if self.priority is not None and (
            isinstance(self.priority, bool) or not isinstance(self.priority, int)
        ):
            raise ValidationError("scheduler priority must be an integer")
        if self.priority is not None and not -1_000 <= self.priority <= 1_000:
            raise ValidationError(
                "scheduler priority must be between -1000 and 1000",
                details={"priority": self.priority},
            )
        if self.timeout_ms is not None and (
            isinstance(self.timeout_ms, bool)
            or not isinstance(self.timeout_ms, int)
            or self.timeout_ms <= 0
        ):
            raise ValidationError(
                "scheduler timeout_ms must be positive when set",
                details={"timeout_ms": self.timeout_ms},
            )
        if self.cancellation is not None and not isinstance(
            self.cancellation, CancellationToken
        ):
            raise ValidationError(
                "scheduler cancellation must be a CancellationToken",
                details={"actual_type": type(self.cancellation).__name__},
            )

    @property
    def resolved_priority(self) -> int:
        if self.priority is not None:
            return self.priority
        return int(
            {
                WorkloadClass.INTERACTIVE: RequestPriority.INTERACTIVE,
                WorkloadClass.STANDARD: RequestPriority.STANDARD,
                WorkloadClass.BACKGROUND: RequestPriority.BACKGROUND,
            }[self.workload]
        )


@dataclass(frozen=True, slots=True)
class SchedulerRequestSnapshot:
    request_id: str
    task_id: str
    sequence: int
    status: SchedulerRequestStatus
    workload: WorkloadClass
    base_priority: int
    effective_priority: int
    queue_position_at_submit: int
    submitted_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    queue_wait_ms: float | None = None
    execution_ms: float | None = None
    timeout_ms: int | None = None
    error_code: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "sequence": self.sequence,
            "status": self.status.value,
            "workload": self.workload.value,
            "base_priority": self.base_priority,
            "effective_priority": self.effective_priority,
            "queue_position_at_submit": self.queue_position_at_submit,
            "submitted_at_utc": self.submitted_at.isoformat(),
            "started_at_utc": self.started_at.isoformat() if self.started_at else None,
            "finished_at_utc": (
                self.finished_at.isoformat() if self.finished_at else None
            ),
            "queue_wait_ms": self.queue_wait_ms,
            "execution_ms": self.execution_ms,
            "timeout_ms": self.timeout_ms,
            "error_code": self.error_code,
        }


@dataclass(frozen=True, slots=True)
class ScheduledExecutionResult:
    value: InferenceResult
    request: SchedulerRequestSnapshot


@dataclass(frozen=True, slots=True)
class SchedulerMetrics:
    policy: SchedulerPolicy
    max_workers: int
    queue_depth: int
    running: int
    peak_queue_depth: int
    submitted: int
    started: int
    completed: int
    cancelled: int
    timed_out: int
    failed: int
    starvation_promotions: int
    queue_wait_p50_ms: float | None
    queue_wait_p95_ms: float | None
    queue_wait_max_ms: float | None
    execution_order: tuple[str, ...] = field(default_factory=tuple)
    requests: tuple[SchedulerRequestSnapshot, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy.value,
            "max_workers": self.max_workers,
            "queue_depth": self.queue_depth,
            "running": self.running,
            "peak_queue_depth": self.peak_queue_depth,
            "submitted": self.submitted,
            "started": self.started,
            "completed": self.completed,
            "cancelled": self.cancelled,
            "timed_out": self.timed_out,
            "failed": self.failed,
            "starvation_promotions": self.starvation_promotions,
            "queue_wait_p50_ms": self.queue_wait_p50_ms,
            "queue_wait_p95_ms": self.queue_wait_p95_ms,
            "queue_wait_max_ms": self.queue_wait_max_ms,
            "execution_order": list(self.execution_order),
            "requests": [request.as_dict() for request in self.requests],
        }
