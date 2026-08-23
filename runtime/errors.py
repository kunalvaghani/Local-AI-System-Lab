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
