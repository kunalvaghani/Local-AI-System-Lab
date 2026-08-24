"""Typed request, schema, permission, and result models for tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from ..errors import ToolArgumentValidationError
from ..models import StateTransition, TaskState


class ToolArgumentType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


@dataclass(frozen=True, slots=True)
class ToolArgumentSpec:
    name: str
    argument_type: ToolArgumentType
    description: str
    required: bool = True
    default: Any = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise ToolArgumentValidationError(
                "tool argument name and description must not be empty"
            )
        if not self.required:
            expected = {
                ToolArgumentType.STRING: str,
                ToolArgumentType.INTEGER: int,
                ToolArgumentType.BOOLEAN: bool,
            }[self.argument_type]
            valid = isinstance(self.default, expected)
            if self.argument_type is ToolArgumentType.INTEGER and isinstance(
                self.default, bool
            ):
                valid = False
            if not valid:
                raise ToolArgumentValidationError(
                    "optional tool argument default has the wrong type",
                    details={
                        "argument": self.name,
                        "expected_type": self.argument_type.value,
                        "actual_type": type(self.default).__name__,
                    },
                )


@dataclass(frozen=True, slots=True)
class ToolPermissionMetadata:
    permissions: frozenset[str]
    read_only: bool
    path_restricted: bool = False
    allowed_roots: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.permissions or any(
            not isinstance(item, str) or not item.strip()
            for item in self.permissions
        ):
            raise ToolArgumentValidationError(
                "a tool must declare at least one non-empty permission"
            )
        if self.path_restricted and not self.allowed_roots:
            raise ToolArgumentValidationError(
                "a path-restricted tool must describe at least one allowed root"
            )


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    arguments: tuple[ToolArgumentSpec, ...]
    permission: ToolPermissionMetadata
    timeout_ms: int = 1_000

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise ToolArgumentValidationError(
                "tool name and description must not be empty"
            )
        names = [argument.name for argument in self.arguments]
        if len(names) != len(set(names)):
            raise ToolArgumentValidationError(
                "tool argument names must be unique",
                details={"tool_name": self.name},
            )
        if self.timeout_ms <= 0:
            raise ToolArgumentValidationError(
                "tool timeout_ms must be positive",
                details={"tool_name": self.name},
            )


@dataclass(frozen=True, slots=True)
class ToolRequest:
    request_id: str
    task_id: str
    agent_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values = {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
        }
        empty = [
            name
            for name, value in values.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if empty or any(not isinstance(key, str) for key in self.arguments):
            raise ToolArgumentValidationError(
                "tool request identity and argument keys must be valid",
                details={"empty_fields": empty},
            )

    @classmethod
    def create(
        cls,
        *,
        task_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> "ToolRequest":
        return cls(
            request_id=str(uuid4()),
            task_id=task_id,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=dict(arguments or {}),
        )


@dataclass(frozen=True, slots=True)
class ToolResult:
    request_id: str
    task_id: str
    agent_id: str
    tool_name: str
    success: bool
    data: dict[str, Any]
    duration_ms: float
    final_state: TaskState | None = None
    state_history: tuple[StateTransition, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "data": dict(self.data),
            "duration_ms": self.duration_ms,
            "final_state": self.final_state.value if self.final_state else None,
            "state_history": [
                {
                    "sequence": item.sequence,
                    "from_state": (
                        item.from_state.value if item.from_state is not None else None
                    ),
                    "to_state": item.to_state.value,
                    "reason": item.reason,
                    "recorded_at_utc": item.recorded_at.isoformat(),
                }
                for item in self.state_history
            ],
        }
