"""Bounded, cooperative tool execution with timeout and cancellation."""

from __future__ import annotations

from queue import Empty, Queue
from threading import Thread
from time import perf_counter

from ..cancellation import CancellationToken
from ..errors import (
    LabError,
    TaskTimeoutError,
    ToolCancelledError,
    ToolExecutionError,
)
from .models import ToolRequest, ToolResult
from .registry import RegisteredTool
from .validation import validate_arguments, validate_result


class ThreadedToolExecutor:
    """Runs handlers on daemon threads; handlers receive a cooperative token."""

    def execute(
        self,
        registered: RegisteredTool,
        request: ToolRequest,
        cancellation: CancellationToken | None = None,
    ) -> ToolResult:
        if registered.definition.name != request.tool_name:
            raise ToolExecutionError(
                "resolved tool does not match the request",
                details={
                    "requested_tool": request.tool_name,
                    "resolved_tool": registered.definition.name,
                },
            )
        arguments = validate_arguments(registered.definition, request.arguments)
        external = cancellation or CancellationToken()
        internal = CancellationToken()
        outcomes: Queue[tuple[str, object]] = Queue(maxsize=1)
        started = perf_counter()

        def invoke() -> None:
            try:
                outcomes.put(("result", registered.handler(arguments, internal)))
            except Exception as error:  # transported back to the caller thread
                outcomes.put(("error", error))

        Thread(
            target=invoke,
            name=f"tool-{request.tool_name}-{request.request_id[:8]}",
            daemon=True,
        ).start()
        timeout_seconds = registered.definition.timeout_ms / 1_000
        deadline = started + timeout_seconds

        while True:
            if external.is_cancelled:
                internal.cancel()
                raise ToolCancelledError(
                    "tool request was cancelled",
                    details={
                        "request_id": request.request_id,
                        "tool_name": request.tool_name,
                    },
                )
            remaining = deadline - perf_counter()
            if remaining <= 0:
                internal.cancel()
                raise TaskTimeoutError(
                    "tool request exceeded its timeout",
                    details={
                        "request_id": request.request_id,
                        "tool_name": request.tool_name,
                        "timeout_ms": registered.definition.timeout_ms,
                    },
                )
            try:
                outcome, payload = outcomes.get(timeout=min(0.01, remaining))
                break
            except Empty:
                continue

        if outcome == "error":
            if isinstance(payload, LabError):
                raise payload
            error = payload
            raise ToolExecutionError(
                "tool handler failed",
                details={
                    "request_id": request.request_id,
                    "tool_name": request.tool_name,
                    "cause_type": type(error).__name__,
                },
            ) from error if isinstance(error, Exception) else None

        data = validate_result(request.tool_name, payload)
        return ToolResult(
            request_id=request.request_id,
            task_id=request.task_id,
            agent_id=request.agent_id,
            tool_name=request.tool_name,
            success=True,
            data=data,
            duration_ms=(perf_counter() - started) * 1_000,
        )
