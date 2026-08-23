"""Replaceable component contracts for the local runtime.

The protocols intentionally contain only behavior exercised by Stage 1.
Later stages may extend them when a demonstrated capability requires it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, runtime_checkable

from .models import (
    Agent,
    Checkpoint,
    InferenceRequest,
    InferenceResult,
    MetricEvent,
    PolicyDecision,
    RouteDecision,
    Task,
)


@runtime_checkable
class InferenceBackend(Protocol):
    @property
    def name(self) -> str: ...

    def start(self) -> None: ...

    def generate(self, request: InferenceRequest) -> InferenceResult: ...

    def shutdown(self) -> None: ...


@runtime_checkable
class Scheduler(Protocol):
    def execute(
        self,
        task: Task,
        operation: Callable[[], InferenceResult],
    ) -> InferenceResult: ...


@runtime_checkable
class ModelRouter(Protocol):
    def route(self, task: Task, agent: Agent) -> RouteDecision: ...


@runtime_checkable
class PolicyEngine(Protocol):
    def evaluate(self, task: Task, agent: Agent) -> PolicyDecision: ...


@runtime_checkable
class CheckpointStore(Protocol):
    def save(self, checkpoint: Checkpoint) -> None: ...

    def latest(self, task_id: str) -> Checkpoint | None: ...


@runtime_checkable
class MetricsCollector(Protocol):
    def record(self, event: MetricEvent) -> None: ...

    def snapshot(self) -> Sequence[MetricEvent]: ...
