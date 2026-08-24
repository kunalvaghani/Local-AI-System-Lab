"""Synchronous, transition-validated orchestration through Stage 11."""

from __future__ import annotations

from dataclasses import dataclass, replace
from time import monotonic
from typing import Any

from .config import RuntimeConfig
from .errors import (
    AdmissionControlError,
    ComputeBudgetExceededError,
    ContextOverflowError,
    InferenceCancelledError,
    InvalidOutputError,
    LabError,
    ModelOutOfMemoryError,
    ModelRoutingError,
    PolicyDeniedError,
    RecoveryNotSupportedError,
    RuntimeLifecycleError,
    TaskExecutionError,
    TaskNotFoundError,
    TaskTimeoutError,
    ToolArgumentValidationError,
    ToolCancelledError,
    ToolExecutionError,
    ValidationError,
)
from .interfaces import (
    AdmissionGate,
    AgentRegistry,
    BudgetPolicy,
    CheckpointStore,
    HardwareProfiler,
    InferenceBackend,
    InferenceController,
    LifecycleEventStore,
    MetricsCollector,
    ModelRouter,
    PolicyEngine,
    RuntimePersistence,
    Scheduler,
    TaskStateMachine,
    ToolExecutor,
    ToolPolicy,
    ToolRegistry,
    TraceStore,
)
from .models import (
    Agent,
    Checkpoint,
    InferenceRequest,
    LifecycleEvent,
    MetricEvent,
    RuntimeStatus,
    StateTransition,
    Task,
    TaskResult,
    TaskState,
)
from .cancellation import CancellationToken
from .tools.models import ToolRequest, ToolResult
from .scheduler.models import SchedulingOptions
from .routing import BudgetUsage, ComputeBudget, RoutingContext
from .tracing import hash_payload, hash_text


@dataclass(frozen=True, slots=True)
class RuntimeComponents:
    agents: AgentRegistry
    inference: InferenceBackend
    scheduler: Scheduler
    router: ModelRouter
    policy: PolicyEngine
    checkpoints: CheckpointStore
    metrics: MetricsCollector
    events: LifecycleEventStore
    state_machine: TaskStateMachine
    tool_registry: ToolRegistry | None = None
    tool_executor: ToolExecutor | None = None
    tool_policy: ToolPolicy | None = None
    admission: AdmissionGate | None = None
    inference_controller: InferenceController | None = None
    budget_policy: BudgetPolicy | None = None
    hardware_profiler: HardwareProfiler | None = None
    persistence: RuntimePersistence | None = None
    traces: TraceStore | None = None


class AgentRuntime:
    """Owns registered-agent execution from task creation through result."""

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
        try:
            self._components.scheduler.start()
        except Exception:
            self._components.inference.shutdown()
            raise
        self._status = RuntimeStatus.RUNNING
        if self._components.persistence is not None:
            self._components.persistence.save_model_configuration(
                self._config.runtime_name,
                self._config.default_model,
                {
                    "runtime_name": self._config.runtime_name,
                    "default_model": self._config.default_model,
                    "max_generated_tokens": self._config.max_generated_tokens,
                },
            )
            for agent in self._components.agents.snapshot():
                self._components.persistence.save_agent(agent)
        self._emit(
            "runtime.started",
            data={"runtime_name": self._config.runtime_name},
        )
        for agent in self._components.agents.snapshot():
            self._emit(
                "agent.available",
                agent=agent,
                data={"name": agent.name},
            )

    def register_agent(self, agent: Agent) -> None:
        self._components.agents.register(agent)
        if self._components.persistence is not None:
            self._components.persistence.save_agent(agent)
        if self._status is RuntimeStatus.RUNNING:
            self._emit(
                "agent.registered",
                agent=agent,
                data={"name": agent.name},
            )

    def available_agents(self) -> tuple[Agent, ...]:
        return tuple(self._components.agents.snapshot())

    def run(
        self,
        *,
        agent_id: str,
        objective: str | None = None,
        input_data: dict[str, Any] | None = None,
        scheduling: SchedulingOptions | None = None,
        compute_budget: ComputeBudget | None = None,
    ) -> TaskResult:
        """Execute a registered specialized agent through all runtime boundaries."""

        self._require_running()
        agent = self._components.agents.get(agent_id)
        resolved_objective = agent.objective if objective is None else objective
        task = self.create_task(
            agent=agent,
            objective=resolved_objective,
            input_data=input_data,
        )
        return self.execute_task(
            task=task,
            agent=agent,
            scheduling=scheduling,
            compute_budget=compute_budget,
        )

    def task_state(self, task_id: str) -> TaskState:
        return self._components.state_machine.current(task_id)

    def state_history(self, task_id: str) -> tuple[StateTransition, ...]:
        return tuple(self._components.state_machine.history(task_id))

    def run_tool(
        self,
        *,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        cancellation: CancellationToken | None = None,
    ) -> ToolResult:
        """Authorize and execute one registered tool as an agent-owned task."""

        self._require_running()
        registry, executor, tool_policy = self._require_tool_components()
        agent = self._components.agents.get(agent_id)
        task = self.create_task(
            agent=agent,
            objective=f"Request tool {tool_name}",
            input_data={"tool_name": tool_name, "arguments": dict(arguments or {})},
        )
        self._transition(
            task,
            agent,
            TaskState.PLANNING,
            reason="runtime began planning tool execution",
        )

        request: ToolRequest | None = None
        try:
            identity = self._components.policy.evaluate(task, agent)
            self._emit(
                "policy.evaluated",
                task=task,
                agent=agent,
                state=TaskState.PLANNING,
                data={"allowed": identity.allowed, "reason": identity.reason},
            )
            if not identity.allowed:
                raise PolicyDeniedError(
                    identity.reason,
                    details={"task_id": task.task_id},
                )

            registered = registry.get(tool_name)
            tool_policy.authorize(agent, registered.definition)
            self._emit(
                "tool.permission.granted",
                task=task,
                agent=agent,
                state=TaskState.PLANNING,
                data={
                    "tool_name": tool_name,
                    "permissions": sorted(
                        registered.definition.permission.permissions
                    ),
                    "read_only": registered.definition.permission.read_only,
                    "path_restricted": (
                        registered.definition.permission.path_restricted
                    ),
                },
            )
            self._transition(
                task,
                agent,
                TaskState.WAITING_FOR_TOOL,
                reason=f"authorized tool request: {tool_name}",
            )
            request = ToolRequest.create(
                task_id=task.task_id,
                agent_id=agent.agent_id,
                tool_name=tool_name,
                arguments=arguments,
            )
            if self._components.persistence is not None:
                self._components.persistence.save_tool_request(request)
            self._emit(
                "tool.invocation.started",
                task=task,
                agent=agent,
                state=TaskState.WAITING_FOR_TOOL,
                data={
                    "request_id": request.request_id,
                    "tool_name": tool_name,
                    "timeout_ms": registered.definition.timeout_ms,
                },
            )
            result = executor.execute(registered, request, cancellation)
            self._emit(
                "tool.invocation.completed",
                task=task,
                agent=agent,
                state=TaskState.WAITING_FOR_TOOL,
                data={
                    "request_id": result.request_id,
                    "tool_name": result.tool_name,
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                },
            )
            self._transition(
                task,
                agent,
                TaskState.VALIDATING,
                reason="tool runtime returned a structured result",
            )
            if (
                not result.success
                or result.task_id != task.task_id
                or result.agent_id != agent.agent_id
                or result.tool_name != tool_name
            ):
                raise InvalidOutputError(
                    "tool result identity or success marker is invalid",
                    details={"task_id": task.task_id, "tool_name": tool_name},
                )
            self._emit(
                "tool.result.validated",
                task=task,
                agent=agent,
                state=TaskState.VALIDATING,
                data={"request_id": result.request_id, "valid": True},
            )
        except LabError as error:
            if request is not None and self._components.persistence is not None:
                self._components.persistence.save_tool_error(request.request_id, error.as_dict())
            self._record_failure(task, agent, error)
            raise
        except Exception as error:
            wrapped = ToolExecutionError(
                "tool execution failed in a runtime component",
                details={
                    "task_id": task.task_id,
                    "tool_name": tool_name,
                    "cause_type": type(error).__name__,
                },
            )
            if request is not None and self._components.persistence is not None:
                self._components.persistence.save_tool_error(request.request_id, wrapped.as_dict())
            self._record_failure(task, agent, wrapped)
            raise wrapped from error

        self._transition(
            task,
            agent,
            TaskState.COMPLETED,
            reason="validated tool result accepted",
        )
        completed = replace(
            result,
            final_state=TaskState.COMPLETED,
            state_history=self.state_history(task.task_id),
        )
        if self._components.persistence is not None:
            self._components.persistence.save_tool_result(completed)
        self._emit(
            "task.completed",
            task=task,
            agent=agent,
            state=TaskState.COMPLETED,
            data={"tool_name": tool_name, "request_id": result.request_id},
        )
        return completed

    def create_task(
        self,
        *,
        agent: Agent,
        objective: str,
        input_data: dict[str, Any] | None = None,
    ) -> Task:
        self._require_running()
        registered = self._components.agents.get(agent.agent_id)
        if registered != agent:
            raise ValidationError(
                "agent definition does not match the registered identity",
                details={"agent_id": agent.agent_id},
            )
        task = Task.create(
            agent_id=agent.agent_id,
            objective=objective,
            input_data=input_data,
        )
        if self._components.persistence is not None:
            self._components.persistence.save_task(task)
        initial = self._components.state_machine.initialize(
            task.task_id,
            reason="runtime created the task",
        )
        self._emit(
            "task.created",
            task=task,
            agent=agent,
            state=TaskState.CREATED,
            data={"objective": objective},
        )
        self._record_transition(task, agent, initial)
        return task

    def prepare_recoverable_task(
        self,
        *,
        agent_id: str,
        objective: str | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> Task:
        """Persist a safe pre-invocation checkpoint for supported recovery."""

        self._require_running()
        if self._components.persistence is None:
            raise RuntimeLifecycleError("recoverable tasks require durable persistence")
        agent = self._components.agents.get(agent_id)
        task = self.create_task(
            agent=agent,
            objective=objective or agent.objective,
            input_data={**dict(input_data or {}), "recovery_mode": "pre_invocation"},
        )
        self._transition(
            task,
            agent,
            TaskState.PLANNING,
            reason="runtime prepared a recoverable execution",
        )
        checkpoint = Checkpoint(
            task_id=task.task_id,
            phase="recovery_ready",
            data={
                "safe_to_retry": True,
                "model_invocation_started": False,
                "tool_invocation_started": False,
            },
        )
        self._components.checkpoints.save(checkpoint)
        self._emit(
            "recovery.checkpoint.ready",
            task=task,
            agent=agent,
            state=TaskState.PLANNING,
            data={"phase": checkpoint.phase, **checkpoint.data},
        )
        return task

    def recover_task(
        self,
        task_id: str,
        *,
        scheduling: SchedulingOptions | None = None,
        compute_budget: ComputeBudget | None = None,
    ) -> TaskResult:
        """Resume one task only from the explicit pre-invocation checkpoint."""

        self._require_running()
        persistence = self._components.persistence
        if persistence is None:
            raise RuntimeLifecycleError("task recovery requires durable persistence")
        candidate = persistence.recovery_candidate(task_id)
        if candidate.disposition.value != "recoverable":
            raise RecoveryNotSupportedError(
                candidate.reason,
                details=candidate.as_dict(),
            )
        task = candidate.task
        agent = self._components.agents.get(task.agent_id)
        attempt_id = persistence.begin_recovery(task_id, candidate.checkpoint.phase)
        self._transition(
            task,
            agent,
            TaskState.RECOVERING,
            reason="runtime restart accepted the durable recovery checkpoint",
        )
        self._emit(
            "recovery.started",
            task=task,
            agent=agent,
            state=TaskState.RECOVERING,
            data={"attempt_id": attempt_id, "checkpoint": candidate.checkpoint.phase},
        )
        try:
            result = self.execute_task(
                task=task,
                agent=agent,
                scheduling=scheduling,
                compute_budget=compute_budget,
            )
        except Exception as error:
            persistence.finish_recovery(
                attempt_id,
                "failed",
                {"cause_type": type(error).__name__},
            )
            raise
        persistence.finish_recovery(
            attempt_id,
            "completed",
            {"final_state": result.final_state.value if result.final_state else None},
        )
        return result

    def execute_task(
        self,
        *,
        task: Task,
        agent: Agent,
        scheduling: SchedulingOptions | None = None,
        compute_budget: ComputeBudget | None = None,
    ) -> TaskResult:
        execution_started = monotonic()
        self._require_running()
        self._components.state_machine.current(task.task_id)
        if task.agent_id != agent.agent_id:
            raise ValidationError(
                "task is assigned to a different agent",
                details={"task_id": task.task_id},
            )
        registered = self._components.agents.get(agent.agent_id)
        if registered != agent:
            raise ValidationError(
                "agent definition does not match the registered identity",
                details={"agent_id": agent.agent_id},
            )

        self._transition(
            task,
            agent,
            TaskState.PLANNING,
            reason="runtime began planning execution",
        )

        try:
            policy = self._components.policy.evaluate(task, agent)
            self._emit(
                "policy.evaluated",
                task=task,
                agent=agent,
                state=TaskState.PLANNING,
                data={"allowed": policy.allowed, "reason": policy.reason},
            )
            if not policy.allowed:
                raise PolicyDeniedError(
                    policy.reason,
                    details={"task_id": task.task_id},
                )

            resolved_scheduling = scheduling or SchedulingOptions()
            resolved_budget = None
            if self._components.budget_policy is not None:
                resolved_budget = self._components.budget_policy.resolve(
                    resolved_scheduling.workload,
                    compute_budget,
                )
                if self._components.hardware_profiler is None:
                    raise RuntimeLifecycleError(
                        "Stage 9 routing requires a hardware profiler"
                    )
                route = self._components.router.route(
                    task,
                    agent,
                    RoutingContext(
                        scheduling=resolved_scheduling,
                        budget=resolved_budget,
                        queue_depth=self._components.scheduler.snapshot().queue_depth,
                        hardware=self._components.hardware_profiler.snapshot(),
                    ),
                )
            else:
                route = self._components.router.route(task, agent)
            self._emit(
                "route.selected",
                task=task,
                agent=agent,
                state=TaskState.PLANNING,
                data=route.as_dict(),
            )
            admission_decision = None
            profile_selection = None
            selected_profile = None
            if self._components.inference_controller is not None:
                profile_selection = self._components.inference_controller.select(
                    task,
                    resolved_scheduling,
                    resolved_budget,
                )
                admission_decision = profile_selection.admission
                selected_profile = profile_selection.selected_profile
                self._emit(
                    "inference.profile.selection.evaluated",
                    task=task,
                    agent=agent,
                    state=TaskState.PLANNING,
                    data=profile_selection.as_dict(),
                )
                self._emit(
                    "admission.evaluated",
                    task=task,
                    agent=agent,
                    state=TaskState.PLANNING,
                    data=admission_decision.as_dict(),
                )
                if not profile_selection.permitted:
                    if profile_selection.budget_limited:
                        raise ComputeBudgetExceededError(
                            profile_selection.reason,
                            details={
                                "task_id": task.task_id,
                                "selection": profile_selection.as_dict(),
                            },
                        )
                    raise AdmissionControlError(
                        profile_selection.reason,
                        details={
                            "task_id": task.task_id,
                            "selection": profile_selection.as_dict(),
                        },
                    )
            elif self._components.admission is not None:
                admission_decision = self._components.admission.evaluate(
                    task,
                    resolved_scheduling,
                )
                self._emit(
                    "admission.evaluated",
                    task=task,
                    agent=agent,
                    state=TaskState.PLANNING,
                    data=admission_decision.as_dict(),
                )
                if not admission_decision.permitted:
                    raise AdmissionControlError(
                        admission_decision.reason,
                        details={
                            "task_id": task.task_id,
                            "decision": admission_decision.as_dict(),
                        },
                    )

            effective_max_tokens = self._config.max_generated_tokens
            budget_preflight: tuple[str, ...] = tuple()
            if resolved_budget is not None:
                violations: list[str] = []
                enforced = ["inference_calls", "generated_tokens", "total_time_ms"]
                if resolved_budget.max_inference_calls < 1:
                    violations.append("max_inference_calls is zero")
                effective_max_tokens = min(
                    effective_max_tokens,
                    resolved_budget.max_generated_tokens,
                )
                if admission_decision is not None:
                    estimate = admission_decision.estimate
                    if resolved_budget.max_ram_mib is not None:
                        enforced.append("predicted_peak_ram_mib")
                        if estimate.predicted_host_ram_mib > resolved_budget.max_ram_mib:
                            violations.append(
                                "predicted host RAM exceeds max_ram_mib"
                            )
                    if resolved_budget.max_vram_mib is not None:
                        enforced.append("predicted_vram_mib")
                        if estimate.predicted_vram_mib > resolved_budget.max_vram_mib:
                            violations.append("predicted VRAM exceeds max_vram_mib")
                elapsed_ms = (monotonic() - execution_started) * 1000.0
                remaining_ms = int(resolved_budget.total_time_ms - elapsed_ms)
                if remaining_ms <= 0:
                    violations.append("total time budget was exhausted during planning")
                budget_preflight = tuple(enforced)
                self._emit(
                    "compute_budget.evaluated",
                    task=task,
                    agent=agent,
                    state=TaskState.PLANNING,
                    data={
                        "permitted": not violations,
                        "budget": resolved_budget.as_dict(),
                        "effective_max_generated_tokens": effective_max_tokens,
                        "remaining_time_ms": max(0, remaining_ms),
                        "enforced": list(budget_preflight),
                        "violations": violations,
                    },
                )
                if violations:
                    raise ComputeBudgetExceededError(
                        "task compute budget rejected execution before scheduling",
                        details={
                            "task_id": task.task_id,
                            "budget": resolved_budget.as_dict(),
                            "violations": violations,
                        },
                    )
                scheduler_timeout = resolved_scheduling.timeout_ms
                resolved_scheduling = replace(
                    resolved_scheduling,
                    timeout_ms=(
                        remaining_ms
                        if scheduler_timeout is None
                        else min(scheduler_timeout, remaining_ms)
                    ),
                )
            self._transition(
                task,
                agent,
                TaskState.EXECUTING,
                reason=f"model route selected: {route.model_id}",
            )
            request = InferenceRequest(
                task_id=task.task_id,
                prompt=task.objective,
                model_id=route.model_id,
                max_generated_tokens=effective_max_tokens,
                system_prompt=agent.system_prompt,
                profile=selected_profile,
            )
            self._emit(
                "scheduler.request.requested",
                task=task,
                agent=agent,
                state=TaskState.EXECUTING,
                data={
                    "workload": resolved_scheduling.workload.value,
                    "priority": resolved_scheduling.resolved_priority,
                    "timeout_ms": resolved_scheduling.timeout_ms,
                },
            )

            def invoke_model(cancellation: CancellationToken):
                self._emit(
                    "model.invocation.started",
                    task=task,
                    agent=agent,
                    state=TaskState.EXECUTING,
                    data={
                        "model_id": route.model_id,
                        "input_hash": hash_payload(
                            {
                                "system_prompt": request.system_prompt,
                                "prompt": request.prompt,
                            }
                        ),
                        "configuration_hash": hash_payload(
                            {
                                "model_id": request.model_id,
                                "max_generated_tokens": request.max_generated_tokens,
                                "profile": (
                                    request.profile.as_dict()
                                    if request.profile is not None
                                    else None
                                ),
                            }
                        ),
                    },
                )
                value = self._components.inference.generate(request, cancellation)
                self._emit(
                    "model.invocation.completed",
                    task=task,
                    agent=agent,
                    state=TaskState.EXECUTING,
                    data={
                        "model_id": value.model_id,
                        "backend_name": value.backend_name,
                        "output_hash": hash_text(value.text),
                    },
                )
                return value

            scheduled_result = self._components.scheduler.execute(
                task,
                invoke_model,
                resolved_scheduling,
            )
            inference_result = scheduled_result.value
            self._emit(
                "scheduler.request.completed",
                task=task,
                agent=agent,
                state=TaskState.EXECUTING,
                data={
                    "request_id": scheduled_result.request.request_id,
                    "workload": scheduled_result.request.workload.value,
                    "priority": scheduled_result.request.base_priority,
                    "effective_priority": (
                        scheduled_result.request.effective_priority
                    ),
                    "queue_wait_ms": scheduled_result.request.queue_wait_ms,
                    "execution_ms": scheduled_result.request.execution_ms,
                },
            )
            self._transition(
                task,
                agent,
                TaskState.VALIDATING,
                reason="model invocation returned a result",
            )
            if not inference_result.text.strip():
                raise InvalidOutputError(
                    "model returned empty output",
                    details={"task_id": task.task_id},
                )
            self._emit(
                "output.validation.completed",
                task=task,
                agent=agent,
                state=TaskState.VALIDATING,
                data={"valid": True},
            )
        except LabError as error:
            self._record_failure(task, agent, error)
            raise
        except Exception as error:
            wrapped = TaskExecutionError(
                "task execution failed in a runtime component",
                details={
                    "task_id": task.task_id,
                    "cause_type": type(error).__name__,
                },
            )
            self._record_failure(task, agent, wrapped)
            raise wrapped from error

        self._transition(
            task,
            agent,
            TaskState.COMPLETED,
            reason="validated model output accepted",
        )

        result = TaskResult(
            task_id=task.task_id,
            output=inference_result.text,
            model_id=inference_result.model_id,
            backend_name=inference_result.backend_name,
            metadata={
                **inference_result.metadata,
                "route_reason": route.reason,
                "route": route.as_dict(),
                "agent_name": agent.name,
                "agent_capabilities": sorted(agent.capabilities),
                "tool_capabilities": [
                    capability.name for capability in agent.tool_capabilities
                ],
                "scheduler": scheduled_result.request.as_dict(),
                "admission": (
                    admission_decision.as_dict()
                    if admission_decision is not None
                    else None
                ),
                "profile_selection": (
                    profile_selection.as_dict()
                    if profile_selection is not None
                    else None
                ),
                "compute_budget": (
                    resolved_budget.as_dict() if resolved_budget is not None else None
                ),
                "compute_usage": (
                    BudgetUsage(
                        inference_calls=1,
                        generated_tokens=(
                            inference_result.metrics.generated_token_runs
                            if inference_result.metrics is not None
                            else None
                        ),
                        elapsed_ms=(monotonic() - execution_started) * 1000.0,
                        peak_ram_mib=(
                            inference_result.metrics.peak_process_ram_mib
                            if inference_result.metrics is not None
                            else None
                        ),
                        vram_delta_mib=(
                            inference_result.metrics.vram_delta_mib
                            if inference_result.metrics is not None
                            else None
                        ),
                        preflight_enforced=budget_preflight,
                    ).as_dict()
                    if resolved_budget is not None
                    else None
                ),
            },
            inference_metrics=inference_result.metrics,
            agent_id=agent.agent_id,
            objective=task.objective,
            final_state=TaskState.COMPLETED,
            state_history=self.state_history(task.task_id),
        )
        if self._components.persistence is not None:
            self._components.persistence.save_task_result(result)
        self._emit(
            "task.completed",
            task=task,
            agent=agent,
            state=TaskState.COMPLETED,
            data={
                "model_id": result.model_id,
                "backend_name": result.backend_name,
            },
        )
        return result

    def shutdown(self) -> None:
        if self._status is RuntimeStatus.STOPPED:
            return
        try:
            try:
                self._components.scheduler.shutdown()
            finally:
                self._components.inference.shutdown()
        finally:
            self._status = RuntimeStatus.STOPPED
            self._emit(
                "runtime.stopped",
                data={"runtime_name": self._config.runtime_name},
            )

    def _require_running(self) -> None:
        if self._status is not RuntimeStatus.RUNNING:
            raise RuntimeLifecycleError("runtime must be started first")

    def _require_tool_components(
        self,
    ) -> tuple[ToolRegistry, ToolExecutor, ToolPolicy]:
        registry = self._components.tool_registry
        executor = self._components.tool_executor
        policy = self._components.tool_policy
        if registry is None or executor is None or policy is None:
            raise RuntimeLifecycleError(
                "runtime tool subsystem is not configured",
                details={"stage_required": 5},
            )
        return registry, executor, policy

    def _record_failure(self, task: Task, agent: Agent, error: LabError) -> None:
        failure_state = self._failure_state(error)
        self._transition(
            task,
            agent,
            failure_state,
            reason=f"execution failed with {error.code}",
        )
        self._emit(
            "task.failed",
            task=task,
            agent=agent,
            state=failure_state,
            data={"error_code": error.code, "error_details": error.details},
        )

    @staticmethod
    def _failure_state(error: LabError) -> TaskState:
        if isinstance(
            error,
            (AdmissionControlError, ComputeBudgetExceededError, ModelRoutingError),
        ):
            return TaskState.RESOURCE_BLOCKED
        if isinstance(error, (InferenceCancelledError, ToolCancelledError)):
            return TaskState.CANCELLED
        if isinstance(error, ModelOutOfMemoryError):
            return TaskState.OUT_OF_MEMORY
        if isinstance(error, ContextOverflowError):
            return TaskState.CONTEXT_OVERFLOW
        if isinstance(error, TaskTimeoutError):
            return TaskState.TIMEOUT
        if isinstance(error, ToolExecutionError):
            return TaskState.TOOL_FAILED
        if isinstance(error, ToolArgumentValidationError):
            return TaskState.TOOL_FAILED
        if isinstance(error, InvalidOutputError):
            return TaskState.INVALID_OUTPUT
        if isinstance(error, PolicyDeniedError):
            return TaskState.SECURITY_BLOCKED
        return TaskState.MODEL_FAILED

    def _transition(
        self,
        task: Task,
        agent: Agent,
        to_state: TaskState,
        *,
        reason: str,
    ) -> StateTransition:
        transition = self._components.state_machine.transition(
            task.task_id,
            to_state,
            reason=reason,
        )
        self._record_transition(task, agent, transition)
        return transition

    def _record_transition(
        self,
        task: Task,
        agent: Agent,
        transition: StateTransition,
    ) -> None:
        self._components.checkpoints.save(
            Checkpoint(
                task_id=task.task_id,
                phase=transition.to_state.value,
                data={
                    "sequence": transition.sequence,
                    "from_state": (
                        transition.from_state.value
                        if transition.from_state is not None
                        else None
                    ),
                    "reason": transition.reason,
                },
            )
        )
        self._emit(
            "task.state.changed",
            task=task,
            agent=agent,
            state=transition.to_state,
            data={
                "sequence": transition.sequence,
                "from_state": (
                    transition.from_state.value
                    if transition.from_state is not None
                    else None
                ),
                "to_state": transition.to_state.value,
                "reason": transition.reason,
                "recorded_at_utc": transition.recorded_at.isoformat(),
            },
        )

    def _emit(
        self,
        name: str,
        *,
        task: Task | None = None,
        agent: Agent | None = None,
        state: TaskState | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        attributes = dict(data or {})
        if state is not None:
            attributes["state"] = state.value
        self._components.events.append(
            LifecycleEvent(
                name=name,
                agent_id=agent.agent_id if agent is not None else None,
                task_id=task.task_id if task is not None else None,
                state=state,
                data=dict(data or {}),
            )
        )
        self._components.metrics.record(
            MetricEvent(
                name=name,
                task_id=task.task_id if task is not None else None,
                attributes=attributes,
            )
        )
    BudgetPolicy,
    HardwareProfiler,
    RecoveryNotSupportedError,
    RuntimePersistence,
