"""Process-local component implementations through Stage 5.

The inference stub remains deliberately fake; registries, stores, routing,
policy, and scheduling are minimal inspectable adapters rather than production
durability, security, concurrency, or observability systems.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from threading import RLock
from time import perf_counter
from uuid import uuid4

from .cancellation import CancellationToken
from .errors import (
    AgentNotFoundError,
    ComponentOperationError,
    DuplicateAgentError,
    InferenceCancelledError,
    SchedulerLifecycleError,
)
from .models import (
    Agent,
    Checkpoint,
    InferenceChunk,
    InferenceMetrics,
    InferenceRequest,
    InferenceResult,
    LifecycleEvent,
    MetricEvent,
    PolicyDecision,
    RouteDecision,
    Task,
    utc_now,
)
from .scheduler.models import (
    ScheduledExecutionResult,
    SchedulerMetrics,
    SchedulerPolicy,
    SchedulerRequestSnapshot,
    SchedulerRequestStatus,
    SchedulingOptions,
)


class InMemoryAgentRegistry:
    """Process-local specialized-agent definitions keyed by stable identity."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}
        self._lock = RLock()

    def register(self, agent: Agent) -> None:
        with self._lock:
            if agent.agent_id in self._agents:
                raise DuplicateAgentError(
                    "agent identity is already registered",
                    details={"agent_id": agent.agent_id},
                )
            self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> Agent:
        with self._lock:
            try:
                return self._agents[agent_id]
            except KeyError as error:
                raise AgentNotFoundError(
                    "agent identity is not registered",
                    details={"agent_id": agent_id},
                ) from error

    def snapshot(self) -> Sequence[Agent]:
        with self._lock:
            return tuple(self._agents.values())


class InMemoryLifecycleEventStore:
    """Append-only, process-local Stage 3 lifecycle evidence."""

    def __init__(self) -> None:
        self._events: list[LifecycleEvent] = []
        self._lock = RLock()

    def append(self, event: LifecycleEvent) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self, task_id: str | None = None) -> Sequence[LifecycleEvent]:
        with self._lock:
            if task_id is None:
                return tuple(self._events)
            return tuple(event for event in self._events if event.task_id == task_id)


class StubInferenceBackend:
    """A deterministic backend that never loads or calls an LLM."""

    def __init__(self, *, response_prefix: str) -> None:
        self._response_prefix = response_prefix
        self._started = False
        self._call_count = 0
        self._last_request: InferenceRequest | None = None

    @property
    def name(self) -> str:
        return "stage-1-stub-backend"

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def last_request(self) -> InferenceRequest | None:
        return self._last_request

    def start(self) -> None:
        if self._started:
            raise ComponentOperationError(
                "stub inference backend is already started",
                details={"component": self.name, "operation": "start"},
            )
        self._started = True

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        if not self._started:
            raise ComponentOperationError(
                "stub inference backend is not started",
                details={"component": self.name, "operation": "generate"},
            )
        chunks = list(self.stream(request, cancellation))
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
        self._last_request = request
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
        self._started = False

    def start(self) -> None:
        if self._started:
            raise SchedulerLifecycleError("inline scheduler is already running")
        self._started = True

    def execute(
        self,
        task: Task,
        operation: Callable[[CancellationToken], InferenceResult],
        options: SchedulingOptions | None = None,
    ) -> ScheduledExecutionResult:
        if not self._started:
            raise SchedulerLifecycleError("inline scheduler is not running")
        resolved = options or SchedulingOptions()
        token = resolved.cancellation or CancellationToken()
        if token.is_cancelled:
            raise InferenceCancelledError(
                "inline scheduler request was cancelled before execution",
                details={"task_id": task.task_id},
            )
        submitted_at = utc_now()
        started = perf_counter()
        self.executed_task_ids.append(task.task_id)
        value = operation(token)
        elapsed_ms = (perf_counter() - started) * 1_000
        return ScheduledExecutionResult(
            value=value,
            request=SchedulerRequestSnapshot(
                request_id=str(uuid4()),
                task_id=task.task_id,
                sequence=len(self.executed_task_ids) - 1,
                status=SchedulerRequestStatus.COMPLETED,
                workload=resolved.workload,
                base_priority=resolved.resolved_priority,
                effective_priority=resolved.resolved_priority,
                queue_position_at_submit=1,
                submitted_at=submitted_at,
                started_at=submitted_at,
                finished_at=utc_now(),
                queue_wait_ms=0.0,
                execution_ms=elapsed_ms,
                timeout_ms=resolved.timeout_ms,
            ),
        )

    def snapshot(self) -> SchedulerMetrics:
        count = len(self.executed_task_ids)
        return SchedulerMetrics(
            policy=SchedulerPolicy.FIFO,
            max_workers=1,
            queue_depth=0,
            running=0,
            peak_queue_depth=0,
            submitted=count,
            started=count,
            completed=count,
            cancelled=0,
            timed_out=0,
            failed=0,
            starvation_promotions=0,
            queue_wait_p50_ms=0.0 if count else None,
            queue_wait_p95_ms=0.0 if count else None,
            queue_wait_max_ms=0.0 if count else None,
            execution_order=tuple(self.executed_task_ids),
        )

    def shutdown(self) -> None:
        self._started = False


class StaticModelRouter:
    """Compatibility router for deterministic and pre-Stage-9 compositions."""

    def __init__(self, *, model_id: str) -> None:
        self._model_id = model_id

    def route(self, task: Task, agent: Agent, context: object | None = None) -> RouteDecision:
        return RouteDecision(
            model_id=self._model_id,
            reason="Static configured route; dynamic model routing is not implemented",
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
            reason="task identity matches; declared tool metadata grants no execution",
        )


class InMemoryCheckpointStore:
    """Process-local lifecycle records with no durability or recovery claims."""

    def __init__(self) -> None:
        self._checkpoints: list[Checkpoint] = []
        self._lock = RLock()

    def save(self, checkpoint: Checkpoint) -> None:
        with self._lock:
            self._checkpoints.append(checkpoint)

    def latest(self, task_id: str) -> Checkpoint | None:
        with self._lock:
            for checkpoint in reversed(self._checkpoints):
                if checkpoint.task_id == task_id:
                    return checkpoint
            return None

    def for_task(self, task_id: str) -> tuple[Checkpoint, ...]:
        with self._lock:
            return tuple(
                checkpoint
                for checkpoint in self._checkpoints
                if checkpoint.task_id == task_id
            )


class InMemoryMetricsCollector:
    """Captures named lifecycle events without a metrics backend."""

    def __init__(self) -> None:
        self._events: list[MetricEvent] = []
        self._lock = RLock()

    def record(self, event: MetricEvent) -> None:
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> Sequence[MetricEvent]:
        with self._lock:
            return tuple(self._events)
