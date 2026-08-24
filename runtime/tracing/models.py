"""Typed Stage 11 execution trace, replay, and comparison records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DeterminismClass(str, Enum):
    """How a trace step may be handled during replay."""

    DETERMINISTIC = "deterministic"
    NONDETERMINISTIC = "nondeterministic"
    SIDE_EFFECTING = "side_effecting"
    OBSERVATIONAL = "observational"


class ReplayOutcome(str, Enum):
    MATCHED = "matched"
    DIVERGED = "diverged"
    OBSERVED_ONLY = "observed_only"
    SKIPPED_SIDE_EFFECT = "skipped_side_effect"
    INTEGRITY_FAILED = "integrity_failed"


@dataclass(frozen=True, slots=True)
class TraceRun:
    run_id: str
    task_id: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    model_id: str | None
    configuration_hash: str | None
    final_chain_hash: str | None
    source_run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "started_at_utc": self.started_at.isoformat(),
            "finished_at_utc": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "model_id": self.model_id,
            "configuration_hash": self.configuration_hash,
            "final_chain_hash": self.final_chain_hash,
            "source_run_id": self.source_run_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class TraceStep:
    run_id: str
    ordinal: int
    step_id: str
    recorded_at: datetime
    actor: str
    component: str
    event_name: str
    determinism: DeterminismClass
    input_data: dict[str, Any]
    input_hash: str
    output_data: dict[str, Any]
    output_hash: str
    semantic_hash: str
    state_from: str | None
    state_to: str | None
    model_id: str | None
    configuration_hash: str | None
    failure: dict[str, Any] | None
    previous_hash: str
    step_hash: str

    def as_dict(self, *, include_payloads: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "run_id": self.run_id,
            "ordinal": self.ordinal,
            "step_id": self.step_id,
            "recorded_at_utc": self.recorded_at.isoformat(),
            "actor": self.actor,
            "component": self.component,
            "event_name": self.event_name,
            "determinism": self.determinism.value,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "semantic_hash": self.semantic_hash,
            "state_from": self.state_from,
            "state_to": self.state_to,
            "model_id": self.model_id,
            "configuration_hash": self.configuration_hash,
            "failure": self.failure,
            "previous_hash": self.previous_hash,
            "step_hash": self.step_hash,
        }
        if include_payloads:
            payload["input"] = self.input_data
            payload["output"] = self.output_data
        return payload


@dataclass(frozen=True, slots=True)
class ReplayStepResult:
    ordinal: int
    step_id: str
    event_name: str
    determinism: DeterminismClass
    outcome: ReplayOutcome
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "step_id": self.step_id,
            "event_name": self.event_name,
            "determinism": self.determinism.value,
            "outcome": self.outcome.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ReplayReport:
    replay_id: str
    source_run_id: str
    started_at: datetime
    finished_at: datetime
    status: str
    integrity_valid: bool
    reconstructed_state: str | None
    steps: tuple[ReplayStepResult, ...]

    def counts(self) -> dict[str, int]:
        counts = {outcome.value: 0 for outcome in ReplayOutcome}
        for step in self.steps:
            counts[step.outcome.value] += 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "source_run_id": self.source_run_id,
            "started_at_utc": self.started_at.isoformat(),
            "finished_at_utc": self.finished_at.isoformat(),
            "status": self.status,
            "integrity_valid": self.integrity_valid,
            "reconstructed_state": self.reconstructed_state,
            "counts": self.counts(),
            "steps": [step.as_dict() for step in self.steps],
        }


@dataclass(frozen=True, slots=True)
class TraceComparisonItem:
    event_name: str
    occurrence: int
    determinism: str
    status: str
    left_step_id: str | None
    right_step_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_name": self.event_name,
            "occurrence": self.occurrence,
            "determinism": self.determinism,
            "status": self.status,
            "left_step_id": self.left_step_id,
            "right_step_id": self.right_step_id,
        }


@dataclass(frozen=True, slots=True)
class TraceComparison:
    left_run_id: str
    right_run_id: str
    model_match: bool
    configuration_match: bool
    deterministic_matches: int
    deterministic_divergences: int
    nondeterministic_observations: int
    missing_steps: int
    items: tuple[TraceComparisonItem, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "left_run_id": self.left_run_id,
            "right_run_id": self.right_run_id,
            "model_match": self.model_match,
            "configuration_match": self.configuration_match,
            "deterministic_matches": self.deterministic_matches,
            "deterministic_divergences": self.deterministic_divergences,
            "nondeterministic_observations": self.nondeterministic_observations,
            "missing_steps": self.missing_steps,
            "items": [item.as_dict() for item in self.items],
        }
