"""Typed unified telemetry reports for Stage 12."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class MetricDistribution:
    count: int
    minimum: float | None
    p50: float | None
    p95: float | None
    maximum: float | None
    mean: float | None
    unit: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "min": self.minimum,
            "p50": self.p50,
            "p95": self.p95,
            "max": self.maximum,
            "mean": self.mean,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class TaskTelemetry:
    task_id: str
    run_id: str | None
    agent_id: str
    state: str | None
    created_at: datetime
    updated_at: datetime
    duration_ms: float
    model_id: str | None
    output_type: str | None
    model_calls: int
    tool_calls: int
    router_decisions: int
    recovery_attempts: int
    trace_steps: int
    queue_wait_ms: float | None
    scheduler_execution_ms: float | None
    inference_metrics: dict[str, Any] | None
    route_reason: str | None
    hardware: dict[str, Any] | None
    failure: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "created_at_utc": self.created_at.isoformat(),
            "updated_at_utc": self.updated_at.isoformat(),
            "duration_ms": self.duration_ms,
            "model_id": self.model_id,
            "output_type": self.output_type,
            "activity": {
                "model_calls": self.model_calls,
                "tool_calls": self.tool_calls,
                "router_decisions": self.router_decisions,
                "recovery_attempts": self.recovery_attempts,
                "trace_steps": self.trace_steps,
            },
            "scheduler": {
                "queue_wait_ms": self.queue_wait_ms,
                "execution_ms": self.scheduler_execution_ms,
            },
            "inference_metrics": self.inference_metrics,
            "route_reason": self.route_reason,
            "hardware": self.hardware,
            "failure": self.failure,
        }


@dataclass(frozen=True, slots=True)
class ObservabilityReport:
    generated_at: datetime
    window_started_at: datetime
    window_ended_at: datetime
    collection_ms: float
    totals: dict[str, Any]
    task_states: dict[str, int]
    distributions: dict[str, MetricDistribution]
    live_scheduler: dict[str, Any] | None
    live_hardware: dict[str, Any] | None
    recent_tasks: tuple[TaskTelemetry, ...]
    recent_events: tuple[dict[str, Any], ...]
    sources: dict[str, str]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at.isoformat(),
            "window": {
                "started_at_utc": self.window_started_at.isoformat(),
                "ended_at_utc": self.window_ended_at.isoformat(),
                "minutes": (self.window_ended_at - self.window_started_at).total_seconds() / 60.0,
            },
            "collection_ms": self.collection_ms,
            "totals": self.totals,
            "task_states": dict(sorted(self.task_states.items())),
            "distributions": {
                name: distribution.as_dict()
                for name, distribution in sorted(self.distributions.items())
            },
            "live": {
                "scheduler": self.live_scheduler,
                "hardware": self.live_hardware,
            },
            "recent_tasks": [task.as_dict() for task in self.recent_tasks],
            "recent_events": list(self.recent_events),
            "sources": dict(sorted(self.sources.items())),
            "warnings": list(self.warnings),
        }
