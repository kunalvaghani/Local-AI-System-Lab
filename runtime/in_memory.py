"""Deterministic Stage 1 component implementations.

These classes prove that the interfaces compose. They are deliberately not real
inference, scheduling, routing, persistence, security, or observability systems.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence

from .cancellation import CancellationToken
from .errors import ComponentOperationError, InferenceCancelledError
from .models import (
    Agent,
    Checkpoint,
    InferenceChunk,
    InferenceMetrics,
    InferenceRequest,
    InferenceResult,
    MetricEvent,
    PolicyDecision,
    RouteDecision,
    Task,
)


class StubInferenceBackend:
    """A deterministic backend that never loads or calls an LLM."""

    def __init__(self, *, response_prefix: str) -> None:
        self._response_prefix = response_prefix
        self._started = False
        self._call_count = 0

    @property
    def name(self) -> str:
        return "stage-1-stub-backend"

    @property
    def call_count(self) -> int:
        return self._call_count

    def start(self) -> None:
        if self._started:
            raise ComponentOperationError(
                "stub inference backend is already started",
                details={"component": self.name, "operation": "start"},
            )
        self._started = True

    def generate(self, request: InferenceRequest) -> InferenceResult:
        if not self._started:
            raise ComponentOperationError(
                "stub inference backend is not started",
                details={"component": self.name, "operation": "generate"},
            )
        chunks = list(self.stream(request))
        return InferenceResult(
            text="".join(chunk.text for chunk in chunks),
            model_id=request.model_id,
            backend_name=self.name,
            metadata={"mode": "stub", "real_llm_calls": 0},
            metrics=chunks[-1].metrics,
        )

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> Iterator[InferenceChunk]:
        if not self._started:
            raise ComponentOperationError(
                "stub inference backend is not started",
                details={"component": self.name, "operation": "stream"},
            )
        if cancellation is not None and cancellation.is_cancelled:
            raise InferenceCancelledError(
                "stub inference was cancelled",
                details={"task_id": request.task_id},
            )
        self._call_count += 1
        text = f"{self._response_prefix} {request.prompt}"
        yield InferenceChunk(text=text)
        yield InferenceChunk(
            is_final=True,
            metrics=InferenceMetrics(total_ms=0.0),
        )

    def shutdown(self) -> None:
        self._started = False


class InlineScheduler:
    """Executes immediately on the caller thread; no queueing or priorities."""

    def __init__(self) -> None:
        self.executed_task_ids: list[str] = []

    def execute(
        self,
        task: Task,
        operation: Callable[[], InferenceResult],
    ) -> InferenceResult:
        self.executed_task_ids.append(task.task_id)
        return operation()


class StaticModelRouter:
    """Selects one logical stub model; dynamic routing is deferred to Stage 9."""

    def __init__(self, *, model_id: str) -> None:
        self._model_id = model_id

    def route(self, task: Task, agent: Agent) -> RouteDecision:
        return RouteDecision(
            model_id=self._model_id,
            reason="Stage 1 static route; dynamic model routing is not implemented",
        )


class IdentityPolicyEngine:
    """Checks task ownership only; this is not a security sandbox."""

    def evaluate(self, task: Task, agent: Agent) -> PolicyDecision:
        if task.agent_id != agent.agent_id:
            return PolicyDecision(
                allowed=False,
                reason="task agent_id does not match the executing agent",
            )
        return PolicyDecision(
            allowed=True,
            reason="task identity matches; tool permissions are not part of Stage 1",
        )


class InMemoryCheckpointStore:
    """Process-local lifecycle records with no durability or recovery claims."""

    def __init__(self) -> None:
        self._checkpoints: list[Checkpoint] = []

    def save(self, checkpoint: Checkpoint) -> None:
        self._checkpoints.append(checkpoint)

    def latest(self, task_id: str) -> Checkpoint | None:
        for checkpoint in reversed(self._checkpoints):
            if checkpoint.task_id == task_id:
                return checkpoint
        return None

    def for_task(self, task_id: str) -> tuple[Checkpoint, ...]:
        return tuple(
            checkpoint
            for checkpoint in self._checkpoints
            if checkpoint.task_id == task_id
        )


class InMemoryMetricsCollector:
    """Captures named lifecycle events without a metrics backend."""

    def __init__(self) -> None:
        self._events: list[MetricEvent] = []

    def record(self, event: MetricEvent) -> None:
        self._events.append(event)

    def snapshot(self) -> Sequence[MetricEvent]:
        return tuple(self._events)
