"""Initial read-only tools constrained to a resolved workspace root."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..cancellation import CancellationToken
from ..errors import (
    ToolArgumentValidationError,
    ToolCancelledError,
    ToolExecutionError,
    ToolPathDeniedError,
)
from .models import (
    ToolArgumentSpec,
    ToolArgumentType,
    ToolDefinition,
    ToolPermissionMetadata,
)
from .registry import InMemoryToolRegistry


_TEXT_SUFFIXES = frozenset({".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"})
_MAX_CHARACTERS = 20_000


def _safe_path(workspace_root: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ToolPathDeniedError(
            "absolute paths are not permitted",
            details={"relative_path": relative_path},
        )
    root = workspace_root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ToolPathDeniedError(
            "path escapes the permitted workspace root",
            details={"relative_path": relative_path, "allowed_root": str(root)},
        ) from error
    if resolved.suffix.lower() not in _TEXT_SUFFIXES:
        raise ToolPathDeniedError(
            "file type is not permitted by the read-only text tool",
            details={"relative_path": relative_path, "suffix": resolved.suffix},
        )
    return resolved


def _read_text(
    workspace_root: Path,
    relative_path: str,
    max_characters: int,
    cancellation: CancellationToken,
) -> dict[str, Any]:
    if not 1 <= max_characters <= _MAX_CHARACTERS:
        raise ToolArgumentValidationError(
            "max_characters is outside the permitted range",
            details={"minimum": 1, "maximum": _MAX_CHARACTERS},
        )
    path = _safe_path(workspace_root, relative_path)
    if cancellation.is_cancelled:
        raise ToolCancelledError("tool was cancelled before filesystem access")
    if not path.is_file():
        raise ToolExecutionError(
            "requested project text file does not exist",
            details={"relative_path": relative_path},
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            text = handle.read(max_characters + 1)
    except (OSError, UnicodeError) as error:
        raise ToolExecutionError(
            "project text file could not be read as UTF-8",
            details={
                "relative_path": relative_path,
                "cause_type": type(error).__name__,
            },
        ) from error
    if cancellation.is_cancelled:
        raise ToolCancelledError("tool was cancelled during filesystem access")
    truncated = len(text) > max_characters
    returned = text[:max_characters]
    return {
        "relative_path": path.relative_to(workspace_root.resolve()).as_posix(),
        "content": returned,
        "characters_returned": len(returned),
        "truncated": truncated,
    }


def build_safe_tool_registry(workspace_root: str | Path) -> InMemoryToolRegistry:
    root = Path(workspace_root).resolve()
    registry = InMemoryToolRegistry()
    permission = ToolPermissionMetadata(
        permissions=frozenset({"filesystem.read"}),
        read_only=True,
        path_restricted=True,
        allowed_roots=("workspace",),
    )
    registry.register(
        ToolDefinition(
            name="project_context_read",
            description="Read a UTF-8 text file contained by the project root.",
            arguments=(
                ToolArgumentSpec(
                    name="relative_path",
                    argument_type=ToolArgumentType.STRING,
                    description="Project-relative path to an approved text file.",
                ),
                ToolArgumentSpec(
                    name="max_characters",
                    argument_type=ToolArgumentType.INTEGER,
                    description="Maximum characters to return (1-20000).",
                    required=False,
                    default=4_000,
                ),
            ),
            permission=permission,
            timeout_ms=1_000,
        ),
        lambda arguments, cancellation: _read_text(
            root,
            arguments["relative_path"],
            arguments["max_characters"],
            cancellation,
        ),
    )
    registry.register(
        ToolDefinition(
            name="risk_register_read",
            description="Read the fixed project risk register.",
            arguments=(
                ToolArgumentSpec(
                    name="max_characters",
                    argument_type=ToolArgumentType.INTEGER,
                    description="Maximum characters to return (1-20000).",
                    required=False,
                    default=4_000,
                ),
            ),
            permission=permission,
            timeout_ms=1_000,
        ),
        lambda arguments, cancellation: _read_text(
            root,
            "docs/risks.md",
            arguments["max_characters"],
            cancellation,
        ),
    )
    return registry
