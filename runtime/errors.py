"""Structured exception hierarchy for runtime boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class LabError(Exception):
    """Base class for expected, serializable project errors."""

    code = "lab_error"

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


class ConfigurationError(LabError):
    code = "configuration_error"


class ValidationError(LabError):
    code = "validation_error"


class RuntimeLifecycleError(LabError):
    code = "runtime_lifecycle_error"


class PolicyDeniedError(LabError):
    code = "policy_denied"


class ComponentOperationError(LabError):
    code = "component_operation_error"


class TaskExecutionError(LabError):
    code = "task_execution_error"


class InferenceCancelledError(LabError):
    code = "inference_cancelled"


class AgentNotFoundError(LabError):
    code = "agent_not_found"


class DuplicateAgentError(LabError):
    code = "duplicate_agent"


class TaskNotFoundError(LabError):
    code = "task_not_found"


class IllegalStateTransitionError(LabError):
    code = "illegal_state_transition"


class InvalidOutputError(TaskExecutionError):
    code = "invalid_output"


class ModelOutOfMemoryError(ComponentOperationError):
    code = "model_out_of_memory"


class ContextOverflowError(ComponentOperationError):
    code = "context_overflow"


class TaskTimeoutError(TaskExecutionError):
    code = "task_timeout"


class ToolExecutionError(ComponentOperationError):
    code = "tool_execution_error"


class ToolNotFoundError(ToolExecutionError):
    code = "tool_not_found"


class DuplicateToolError(ValidationError):
    code = "duplicate_tool"


class ToolArgumentValidationError(ValidationError):
    code = "tool_argument_validation_error"


class ToolPermissionDeniedError(PolicyDeniedError):
    code = "tool_permission_denied"


class ToolPathDeniedError(PolicyDeniedError):
    code = "tool_path_denied"


class ToolCancelledError(TaskExecutionError):
    code = "tool_cancelled"


class ToolResultValidationError(InvalidOutputError):
    code = "tool_result_validation_error"


class SchedulerLifecycleError(RuntimeLifecycleError):
    code = "scheduler_lifecycle_error"


class SchedulerCancelledError(InferenceCancelledError):
    code = "scheduler_cancelled"


class AdmissionControlError(TaskExecutionError):
    """A workload was not admitted with its currently configured resources."""

    code = "admission_controlled"


class ModelRoutingError(TaskExecutionError):
    """No registered model satisfied the current routing constraints."""

    code = "model_routing_failed"


class ComputeBudgetExceededError(TaskExecutionError):
    """Execution would exceed an explicit task compute budget."""

    code = "compute_budget_exceeded"


class RecoveryNotSupportedError(TaskExecutionError):
    """A durable task is not at a checkpoint that can be retried safely."""

    code = "recovery_not_supported"
