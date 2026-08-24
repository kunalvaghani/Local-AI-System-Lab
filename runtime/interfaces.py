"""Replaceable component contracts for the local runtime through Stage 12."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Any, Protocol, runtime_checkable

from .cancellation import CancellationToken
from .models import (
    Agent,
    Checkpoint,
    InferenceChunk,
    InferenceRequest,
    InferenceResult,
    LifecycleEvent,
    MetricEvent,
    PolicyDecision,
    RouteDecision,
    StateTransition,
    Task,
    TaskResult,
    TaskState,
)
from .tools.models import ToolDefinition, ToolRequest, ToolResult
from .tools.registry import RegisteredTool, ToolHandler
from .scheduler.models import (
    ScheduledExecutionResult,
    SchedulerMetrics,
    SchedulingOptions,
)
from .hardware.models import AdmissionDecision
from .hardware.models import HardwareSnapshot
from .adaptive.models import ProfileSelection
from .routing.models import ComputeBudget, RoutingContext
from .tracing.models import ReplayReport, TraceRun, TraceStep
from .observability.models import ObservabilityReport


@runtime_checkable
class AgentRegistry(Protocol):
    def register(self, agent: Agent) -> None: ...

    def get(self, agent_id: str) -> Agent: ...

    def snapshot(self) -> Sequence[Agent]: ...


@runtime_checkable
class LifecycleEventStore(Protocol):
    def append(self, event: LifecycleEvent) -> None: ...

    def snapshot(self, task_id: str | None = None) -> Sequence[LifecycleEvent]: ...


@runtime_checkable
class TaskStateMachine(Protocol):
    def initialize(self, task_id: str, *, reason: str) -> StateTransition: ...

    def transition(
        self,
        task_id: str,
        to_state: TaskState,
        *,
        reason: str,
    ) -> StateTransition: ...

    def current(self, task_id: str) -> TaskState: ...

    def history(self, task_id: str) -> Sequence[StateTransition]: ...


@runtime_checkable
class InferenceBackend(Protocol):
    @property
    def name(self) -> str: ...

    def start(self) -> None: ...

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult: ...

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> Iterator[InferenceChunk]: ...

    def shutdown(self) -> None: ...


@runtime_checkable
class Scheduler(Protocol):
    def start(self) -> None: ...

    def execute(
        self,
        task: Task,
        operation: Callable[[CancellationToken], InferenceResult],
        options: SchedulingOptions | None = None,
    ) -> ScheduledExecutionResult: ...

    def snapshot(self) -> SchedulerMetrics: ...

    def shutdown(self) -> None: ...


@runtime_checkable
class ModelRouter(Protocol):
    def route(
        self,
        task: Task,
        agent: Agent,
        context: RoutingContext | None = None,
    ) -> RouteDecision: ...


@runtime_checkable
class BudgetPolicy(Protocol):
    def resolve(
        self,
        workload: "WorkloadClass",
        override: ComputeBudget | None = None,
    ) -> ComputeBudget: ...


@runtime_checkable
class PolicyEngine(Protocol):
    def evaluate(self, task: Task, agent: Agent) -> PolicyDecision: ...


@runtime_checkable
class AdmissionGate(Protocol):
    def evaluate(
        self,
        task: Task,
        scheduling: SchedulingOptions,
    ) -> AdmissionDecision: ...


@runtime_checkable
class HardwareProfiler(Protocol):
    def snapshot(self) -> HardwareSnapshot: ...


@runtime_checkable
class InferenceController(Protocol):
    def select(
        self,
        task: Task,
        scheduling: SchedulingOptions,
        budget: ComputeBudget | None = None,
    ) -> ProfileSelection: ...


@runtime_checkable
class CheckpointStore(Protocol):
    def save(self, checkpoint: Checkpoint) -> None: ...

    def latest(self, task_id: str) -> Checkpoint | None: ...


@runtime_checkable
class RuntimePersistence(Protocol):
    @property
    def schema_version(self) -> int: ...

    def save_agent(self, agent: Agent) -> None: ...

    def save_task(self, task: Task) -> None: ...

    def load_task(self, task_id: str) -> Task: ...

    def save_model_configuration(
        self,
        runtime_name: str,
        model_id: str,
        payload: dict[str, Any],
    ) -> None: ...

    def save_task_result(self, result: TaskResult) -> None: ...

    def save_tool_request(self, request: ToolRequest) -> None: ...

    def save_tool_result(self, result: ToolResult) -> None: ...

    def save_tool_error(self, request_id: str, error: dict[str, Any]) -> None: ...

    def recovery_candidate(self, task_id: str) -> Any: ...

    def begin_recovery(self, task_id: str, checkpoint_phase: str) -> int: ...

    def finish_recovery(
        self,
        attempt_id: int,
        status: str,
        details: dict[str, Any],
    ) -> None: ...

    def table_counts(self) -> dict[str, int]: ...

    def integrity_check(self) -> str: ...


@runtime_checkable
class TraceStore(Protocol):
    def for_task(self, task_id: str) -> TraceRun: ...

    def load_run(self, run_id: str) -> TraceRun: ...

    def steps(self, run_id: str) -> Sequence[TraceStep]: ...

    def list_runs(self) -> Sequence[TraceRun]: ...

    def save_replay(self, report: ReplayReport) -> None: ...


@runtime_checkable
class ObservabilityBackend(Protocol):
    def report(
        self,
        *,
        window_minutes: int | None = None,
        recent_task_limit: int | None = None,
        recent_event_limit: int | None = None,
        include_live: bool = True,
    ) -> ObservabilityReport: ...


@runtime_checkable
class MetricsCollector(Protocol):
    def record(self, event: MetricEvent) -> None: ...

    def snapshot(self) -> Sequence[MetricEvent]: ...


@runtime_checkable
class ToolRegistry(Protocol):
    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None: ...

    def get(self, tool_name: str) -> RegisteredTool: ...

    def snapshot(self) -> Sequence[ToolDefinition]: ...


@runtime_checkable
class ToolExecutor(Protocol):
    def execute(
        self,
        registered: RegisteredTool,
        request: ToolRequest,
        cancellation: CancellationToken | None = None,
    ) -> ToolResult: ...


@runtime_checkable
class ToolPolicy(Protocol):
    def authorize(self, agent: Agent, definition: ToolDefinition) -> None: ...
