"""Typed transport-facing records for Stage 15."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..cancellation import CancellationToken
from ..models import Task, TaskResult, utc_now


class ApiTaskStatus(str, Enum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


def result_payload(result: TaskResult) -> dict[str, Any]:
    return {
        "task_id": result.task_id,
        "agent_id": result.agent_id,
        "objective": result.objective,
        "output": result.output,
        "model_id": result.model_id,
        "backend_name": result.backend_name,
        "final_state": result.final_state.value if result.final_state else None,
        "metadata": dict(result.metadata),
        "inference_metrics": (
            result.inference_metrics.as_dict() if result.inference_metrics else None
        ),
        "state_history": [
            {
                "sequence": item.sequence,
                "from_state": item.from_state.value if item.from_state else None,
                "to_state": item.to_state.value,
                "reason": item.reason,
                "recorded_at_utc": item.recorded_at.isoformat(),
            }
            for item in result.state_history
        ],
    }


@dataclass(slots=True)
class ApiTaskRecord:
    task: Task
    cancellation: CancellationToken
    status: ApiTaskStatus = ApiTaskStatus.ACCEPTED
    accepted_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: TaskResult | None = None
    error: dict[str, Any] | None = None
    cancellation_requested: bool = False

    @property
    def terminal(self) -> bool:
        return self.status in {
            ApiTaskStatus.COMPLETED,
            ApiTaskStatus.FAILED,
            ApiTaskStatus.CANCELLED,
            ApiTaskStatus.TIMED_OUT,
        }

    def as_dict(self, *, durable_state: str | None = None) -> dict[str, Any]:
        return {
            "task_id": self.task.task_id,
            "agent_id": self.task.agent_id,
            "objective": self.task.objective,
            "input_data": dict(self.task.input_data),
            "status": self.status.value,
            "durable_state": durable_state,
            "cancellation_requested": self.cancellation_requested,
            "accepted_at_utc": self.accepted_at.isoformat(),
            "started_at_utc": self.started_at.isoformat() if self.started_at else None,
            "finished_at_utc": self.finished_at.isoformat() if self.finished_at else None,
            "result": result_payload(self.result) if self.result else None,
            "error": dict(self.error) if self.error else None,
            "links": {
                "self": f"/v1/tasks/{self.task.task_id}",
                "events": f"/v1/tasks/{self.task.task_id}/events",
                "trace": f"/v1/tasks/{self.task.task_id}/trace",
            },
        }
