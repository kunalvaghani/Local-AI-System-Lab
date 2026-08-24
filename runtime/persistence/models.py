"""Typed Stage 10 persistence and recovery evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from ..models import Checkpoint, Task, TaskState


class RecoveryDisposition(str, Enum):
    RECOVERABLE = "recoverable"
    TERMINAL = "terminal"
    UNSAFE_TO_RETRY = "unsafe_to_retry"
    INVALID_CHECKPOINT = "invalid_checkpoint"


@dataclass(frozen=True, slots=True)
class RecoveryCandidate:
    task: Task
    state: TaskState
    checkpoint: Checkpoint | None
    disposition: RecoveryDisposition
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task.task_id,
            "agent_id": self.task.agent_id,
            "state": self.state.value,
            "checkpoint": (
                {
                    "phase": self.checkpoint.phase,
                    "recorded_at_utc": self.checkpoint.recorded_at.isoformat(),
                    "data": self.checkpoint.data,
                }
                if self.checkpoint is not None
                else None
            ),
            "disposition": self.disposition.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class RecoveryAttempt:
    attempt_id: int
    task_id: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    checkpoint_phase: str
    details: dict[str, Any]
