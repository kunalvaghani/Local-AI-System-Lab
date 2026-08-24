"""Strict, non-coercing validation for tool arguments and results."""

from __future__ import annotations

from typing import Any

from ..errors import ToolArgumentValidationError, ToolResultValidationError
from .models import ToolArgumentType, ToolDefinition


_EXPECTED_TYPES: dict[ToolArgumentType, type[Any]] = {
    ToolArgumentType.STRING: str,
    ToolArgumentType.INTEGER: int,
    ToolArgumentType.BOOLEAN: bool,
}


def validate_arguments(
    definition: ToolDefinition,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    specs = {item.name: item for item in definition.arguments}
    unknown = sorted(set(arguments) - set(specs))
    if unknown:
        raise ToolArgumentValidationError(
            "tool request contains unknown arguments",
            details={"tool_name": definition.name, "unknown_arguments": unknown},
        )

    validated: dict[str, Any] = {}
    for name, spec in specs.items():
        if name not in arguments:
            if spec.required:
                raise ToolArgumentValidationError(
                    "tool request is missing a required argument",
                    details={"tool_name": definition.name, "argument": name},
                )
            validated[name] = spec.default
            continue
        value = arguments[name]
        expected = _EXPECTED_TYPES[spec.argument_type]
        valid = isinstance(value, expected)
        if spec.argument_type is ToolArgumentType.INTEGER and isinstance(value, bool):
            valid = False
        if not valid:
            raise ToolArgumentValidationError(
                "tool argument has the wrong type",
                details={
                    "tool_name": definition.name,
                    "argument": name,
                    "expected_type": spec.argument_type.value,
                    "actual_type": type(value).__name__,
                },
            )
        validated[name] = value
    return validated


def validate_result(tool_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) for key in value
    ):
        raise ToolResultValidationError(
            "tool handler returned an invalid result",
            details={"tool_name": tool_name, "expected": "dict[str, Any]"},
        )
    return dict(value)
