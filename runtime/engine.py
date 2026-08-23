"""Lifecycle orchestration for the Stage 1 runtime skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import RuntimeConfig
from .errors import (
    LabError,
    PolicyDeniedError,
    RuntimeLifecycleError,
    TaskExecutionError,
    ValidationError,
)
from .interfaces import (
    CheckpointStore,
    InferenceBackend,
    MetricsCollector,
    ModelRouter,
    PolicyEngine,
    Scheduler,
)
from .models import (
    Agent,
    Checkpoint,
    InferenceRequest,
    MetricEvent,
    RuntimeStatus,
    Task,
    TaskResult,
)


@dataclass(frozen=True, slots=True)
class RuntimeComponents:
    inference: InferenceBackend
    scheduler: Scheduler
    router: ModelRouter
    policy: PolicyEngine
    checkpoints: CheckpointStore
    metrics: MetricsCollector


class AgentRuntime:
    """Composes Stage 1 interfaces into one minimal synchronous lifecycle."""

    def __init__(
        self,
        *,
        config: RuntimeConfig,
        components: RuntimeComponents,
    ) -> None:
        self._config = config
        self._components = components
        self._status = RuntimeStatus.STOPPED

    @property
    def config(self) -> RuntimeConfig:
        return self._config

    @property
    def components(self) -> RuntimeComponents:
        return self._components

    @property
    def status(self) -> RuntimeStatus:
        return self._status

    def start(self) -> None:
        if self._status is RuntimeStatus.RUNNING:
            raise RuntimeLifecycleError("runtime is already running")
        self._components.inference.start()
        self._status = RuntimeStatus.RUNNING
        self._components.metrics.record(
            MetricEvent(
                name="runtime.started",
                attributes={"runtime_name": self._config.runtime_name},
            )
        )

    def create_task(
        self,
        *,
        agent: Agent,
        objective: str,
        input_data: dict[str, Any] | None = None,
    ) -> Task:
        self._require_running()
        task = Task.create(
            agent_id=agent.agent_id,
            objective=objective,
            input_data=input_data,
        )
        self._components.checkpoints.save(
            Checkpoint(task_id=task.task_id, phase="created")
        )
        self._components.metrics.record(
            MetricEvent(name="task.created", task_id=task.task_id)
        )
        return task

    def execute_task(self, *, task: Task, agent: Agent) -> TaskResult:
        self._require_running()
        if task.agent_id != agent.agent_id:
            raise ValidationError(
                "task is assigned to a different agent",
                details={"task_id": task.task_id},
            )

        policy = self._components.policy.evaluate(task, agent)
        self._components.metrics.record(
            MetricEvent(
                name="policy.evaluated",
                task_id=task.task_id,
                attributes={"allowed": policy.allowed, "reason": policy.reason},
            )
        )
        if not policy.allowed:
            self._components.checkpoints.save(
                Checkpoint(
                    task_id=task.task_id,
                    phase="denied",
                    data={"reason": policy.reason},
                )
            )
            raise PolicyDeniedError(
                policy.reason,
                details={"task_id": task.task_id},
            )

        route = self._components.router.route(task, agent)
        self._components.metrics.record(
            MetricEvent(
                name="route.selected",
                task_id=task.task_id,
                attributes={"model_id": route.model_id, "reason": route.reason},
            )
        )
        self._components.checkpoints.save(
            Checkpoint(
                task_id=task.task_id,
                phase="executing",
                data={"model_id": route.model_id},
            )
        )

        request = InferenceRequest(
            task_id=task.task_id,
            prompt=task.objective,
            model_id=route.model_id,
            max_generated_tokens=self._config.max_generated_tokens,
        )
        try:
            inference_result = self._components.scheduler.execute(
                task,
                lambda: self._components.inference.generate(request),
            )
        except LabError as error:
            self._record_failure(task, error)
            raise
        except Exception as error:
            wrapped = TaskExecutionError(
                "task execution failed in a runtime component",
                details={
                    "task_id": task.task_id,
                    "cause_type": type(error).__name__,
                },
            )
            self._record_failure(task, wrapped)
            raise wrapped from error

        result = TaskResult(
            task_id=task.task_id,
            output=inference_result.text,
            model_id=inference_result.model_id,
            backend_name=inference_result.backend_name,
            metadata={
                **inference_result.metadata,
                "route_reason": route.reason,
            },
        )
        self._components.checkpoints.save(
            Checkpoint(
                task_id=task.task_id,
                phase="completed",
                data={
                    "model_id": result.model_id,
                    "backend_name": result.backend_name,
                },
            )
        )
        self._components.metrics.record(
            MetricEvent(
                name="task.completed",
                task_id=task.task_id,
                attributes={
                    "model_id": result.model_id,
                    "backend_name": result.backend_name,
                },
            )
        )
        return result

    def shutdown(self) -> None:
        if self._status is RuntimeStatus.STOPPED:
            return
        try:
            self._components.inference.shutdown()
        finally:
            self._status = RuntimeStatus.STOPPED
            self._components.metrics.record(
                MetricEvent(
                    name="runtime.stopped",
                    attributes={"runtime_name": self._config.runtime_name},
                )
            )

    def _require_running(self) -> None:
        if self._status is not RuntimeStatus.RUNNING:
            raise RuntimeLifecycleError("runtime must be started first")

    def _record_failure(self, task: Task, error: LabError) -> None:
        self._components.checkpoints.save(
            Checkpoint(
                task_id=task.task_id,
                phase="failed",
                data={"error_code": error.code},
            )
        )
        self._components.metrics.record(
            MetricEvent(
                name="task.failed",
                task_id=task.task_id,
                attributes={"error_code": error.code},
            )
        )
