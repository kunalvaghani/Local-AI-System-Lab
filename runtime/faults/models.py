"""Typed deterministic fault plans and measurable Stage 13 reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..errors import ConfigurationError


class FaultKind(str, Enum):
    MODEL_TIMEOUT = "model_timeout"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    CONTEXT_OVERFLOW = "context_overflow"
    SIMULATED_OOM = "simulated_oom"
    TOOL_TIMEOUT = "tool_timeout"
    CORRUPTED_TOOL_RESULT = "corrupted_tool_result"
    MALFORMED_TOOL_CALL = "malformed_tool_call"
    DATABASE_RESULT_FAILURE = "database_result_failure"
    AGENT_CRASH = "agent_crash"


class FaultPoint(str, Enum):
    INFERENCE_GENERATE = "inference.generate"
    TOOL_EXECUTE = "tool.execute"
    PERSISTENCE_SAVE_RESULT = "persistence.save_task_result"
    RECOVERY_CHECKPOINT = "recovery.checkpoint_ready"


FAULT_POINTS: dict[FaultKind, FaultPoint] = {
    FaultKind.MODEL_TIMEOUT: FaultPoint.INFERENCE_GENERATE,
    FaultKind.INVALID_MODEL_OUTPUT: FaultPoint.INFERENCE_GENERATE,
    FaultKind.CONTEXT_OVERFLOW: FaultPoint.INFERENCE_GENERATE,
    FaultKind.SIMULATED_OOM: FaultPoint.INFERENCE_GENERATE,
    FaultKind.TOOL_TIMEOUT: FaultPoint.TOOL_EXECUTE,
    FaultKind.CORRUPTED_TOOL_RESULT: FaultPoint.TOOL_EXECUTE,
    FaultKind.MALFORMED_TOOL_CALL: FaultPoint.TOOL_EXECUTE,
    FaultKind.DATABASE_RESULT_FAILURE: FaultPoint.PERSISTENCE_SAVE_RESULT,
    FaultKind.AGENT_CRASH: FaultPoint.RECOVERY_CHECKPOINT,
}


@dataclass(frozen=True, slots=True)
class FaultScenario:
    scenario_id: str
    kind: FaultKind
    delay_ms: int = 0
    max_injections: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ConfigurationError("fault scenario_id must not be empty")
        if isinstance(self.delay_ms, bool) or not isinstance(self.delay_ms, int) or self.delay_ms < 0:
            raise ConfigurationError("fault delay_ms must be a non-negative integer")
        if (
            isinstance(self.max_injections, bool)
            or not isinstance(self.max_injections, int)
            or self.max_injections <= 0
        ):
            raise ConfigurationError("fault max_injections must be a positive integer")

    @property
    def point(self) -> FaultPoint:
        return FAULT_POINTS[self.kind]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "kind": self.kind.value,
            "point": self.point.value,
            "delay_ms": self.delay_ms,
            "max_injections": self.max_injections,
        }


@dataclass(frozen=True, slots=True)
class FaultPlan:
    armed: bool = False
    scenarios: tuple[FaultScenario, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.armed, bool):
            raise ConfigurationError("fault plan armed must be boolean")
        identifiers = [scenario.scenario_id for scenario in self.scenarios]
        if len(identifiers) != len(set(identifiers)):
            raise ConfigurationError("fault scenario IDs must be unique")


@dataclass(frozen=True, slots=True)
class FaultRecord:
    scenario_id: str
    kind: FaultKind
    point: FaultPoint
    occurrence: int
    task_id: str | None
    injected_at: datetime
    delay_ms: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "kind": self.kind.value,
            "point": self.point.value,
            "occurrence": self.occurrence,
            "task_id": self.task_id,
            "injected_at_utc": self.injected_at.isoformat(),
            "delay_ms": self.delay_ms,
        }


@dataclass(frozen=True, slots=True)
class ChaosScenarioResult:
    scenario_id: str
    kind: str
    target: str
    task_id: str | None
    expected_state: str | None
    actual_state: str | None
    expected_error_code: str | None
    actual_error_code: str | None
    injected: bool
    injection_count: int
    duration_ms: float
    baseline_ms: float
    added_latency_ms: float
    recovery_attempted: bool
    recovery_succeeded: bool | None
    contained: bool
    expected_outcome_met: bool
    trace_steps: int
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "kind": self.kind,
            "target": self.target,
            "task_id": self.task_id,
            "expected": {
                "state": self.expected_state,
                "error_code": self.expected_error_code,
            },
            "actual": {
                "state": self.actual_state,
                "error_code": self.actual_error_code,
            },
            "injected": self.injected,
            "injection_count": self.injection_count,
            "duration_ms": self.duration_ms,
            "baseline_ms": self.baseline_ms,
            "added_latency_ms": self.added_latency_ms,
            "recovery": {
                "attempted": self.recovery_attempted,
                "succeeded": self.recovery_succeeded,
            },
            "contained": self.contained,
            "expected_outcome_met": self.expected_outcome_met,
            "trace_steps": self.trace_steps,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ChaosReport:
    run_id: str
    database: str
    started_at: datetime
    finished_at: datetime
    baselines_ms: dict[str, float]
    scenarios: tuple[ChaosScenarioResult, ...]
    observability: dict[str, Any]
    database_integrity: str
    real_llm_calls: int = 0

    def as_dict(self) -> dict[str, Any]:
        attempted_recoveries = sum(item.recovery_attempted for item in self.scenarios)
        successful_recoveries = sum(item.recovery_succeeded is True for item in self.scenarios)
        completed = sum(item.actual_state == "completed" and item.actual_error_code is None for item in self.scenarios)
        contained = sum(item.contained for item in self.scenarios)
        matched = sum(item.expected_outcome_met for item in self.scenarios)
        total = len(self.scenarios)
        added = sorted(item.added_latency_ms for item in self.scenarios)

        def percentile(quantile: float) -> float | None:
            if not added:
                return None
            if len(added) == 1:
                return added[0]
            position = (len(added) - 1) * quantile
            lower = int(position)
            upper = min(lower + 1, len(added) - 1)
            fraction = position - lower
            return added[lower] + (added[upper] - added[lower]) * fraction

        return {
            "stage": 13,
            "purpose": "deliberately inject bounded subsystem faults and measure containment and safe recovery",
            "run_id": self.run_id,
            "database": self.database,
            "started_at_utc": self.started_at.isoformat(),
            "finished_at_utc": self.finished_at.isoformat(),
            "duration_ms": (self.finished_at - self.started_at).total_seconds() * 1000.0,
            "armed": True,
            "baselines_ms": dict(sorted(self.baselines_ms.items())),
            "summary": {
                "scenarios": total,
                "injections": sum(item.injection_count for item in self.scenarios),
                "expected_outcomes_met": matched,
                "expected_outcome_rate_percent": matched / total * 100.0 if total else None,
                "contained": contained,
                "containment_rate_percent": contained / total * 100.0 if total else None,
                "completed_without_error": completed,
                "task_completion_rate_percent": completed / total * 100.0 if total else None,
                "recovery_attempts": attempted_recoveries,
                "recovery_successes": successful_recoveries,
                "recovery_success_rate_percent": (
                    successful_recoveries / attempted_recoveries * 100.0
                    if attempted_recoveries
                    else None
                ),
                "real_llm_calls": self.real_llm_calls,
                "quality_impact": None,
                "quality_impact_reason": "deterministic fault containment has no meaningful semantic quality score",
                "added_latency_ms": {
                    "count": len(added),
                    "min": min(added) if added else None,
                    "p50": percentile(0.50),
                    "p95": percentile(0.95),
                    "max": max(added) if added else None,
                    "mean": sum(added) / len(added) if added else None,
                },
            },
            "scenarios": [item.as_dict() for item in self.scenarios],
            "observability": self.observability,
            "database_integrity": self.database_integrity,
        }
