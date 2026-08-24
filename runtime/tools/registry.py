"""Process-local tool registry with duplicate and missing-tool errors."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from ..cancellation import CancellationToken
from ..errors import DuplicateToolError, ToolNotFoundError
from .models import ToolDefinition


ToolHandler = Callable[[dict[str, Any], CancellationToken], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    definition: ToolDefinition
    handler: ToolHandler


class InMemoryToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        if definition.name in self._tools:
            raise DuplicateToolError(
                "tool name is already registered",
                details={"tool_name": definition.name},
            )
        self._tools[definition.name] = RegisteredTool(definition, handler)

    def get(self, tool_name: str) -> RegisteredTool:
        try:
            return self._tools[tool_name]
        except KeyError as error:
            raise ToolNotFoundError(
                "tool is not registered",
                details={"tool_name": tool_name},
            ) from error

    def snapshot(self) -> Sequence[ToolDefinition]:
        return tuple(tool.definition for tool in self._tools.values())
