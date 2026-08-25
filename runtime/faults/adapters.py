"""Protocol-level fault adapters; inert unless an explicit plan is armed."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterator

from ..cancellation import CancellationToken
from ..errors import (
    ContextOverflowError,
    DatabaseOperationError,
    ModelOutOfMemoryError,
    TaskTimeoutError,
)
from ..models import InferenceChunk, InferenceRequest, InferenceResult, TaskResult
from ..tools.models import ToolRequest, ToolResult
from ..tools.registry import RegisteredTool
from .controller import FaultController
from .models import FaultKind, FaultPoint, FaultScenario


def _details(scenario: FaultScenario, task_id: str | None) -> dict[str, Any]:
    return {"injected_fault": scenario.as_dict(), "task_id": task_id}


class FaultInjectingInferenceBackend:
    def __init__(self, delegate: Any, controller: FaultController) -> None:
        self._delegate = delegate
        self._controller = controller

    @property
    def name(self) -> str:
        return self._delegate.name

    @property
    def call_count(self) -> int:
        return int(getattr(self._delegate, "call_count", 0))

    def start(self) -> None:
        self._delegate.start()

    def _activate(self, task_id: str) -> FaultScenario | None:
        scenario = self._controller.trigger(
            FaultPoint.INFERENCE_GENERATE,
            task_id=task_id,
        )
        if scenario is None:
            return None
        details = _details(scenario, task_id)
        if scenario.kind is FaultKind.MODEL_TIMEOUT:
            raise TaskTimeoutError("injected model timeout", details=details)
        if scenario.kind is FaultKind.CONTEXT_OVERFLOW:
            raise ContextOverflowError("injected context overflow", details=details)
        if scenario.kind is FaultKind.SIMULATED_OOM:
            raise ModelOutOfMemoryError("injected model out-of-memory", details=details)
        return scenario

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        scenario = self._activate(request.task_id)
        result = self._delegate.generate(request, cancellation)
        if scenario is not None and scenario.kind is FaultKind.INVALID_MODEL_OUTPUT:
            return replace(
                result,
                text=" ",
                metadata={**result.metadata, "injected_fault": scenario.as_dict()},
            )
        return result

    def stream(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> Iterator[InferenceChunk]:
        scenario = self._activate(request.task_id)
        if scenario is not None and scenario.kind is FaultKind.INVALID_MODEL_OUTPUT:
            for chunk in self._delegate.stream(request, cancellation):
                yield replace(chunk, text="")
            return
        yield from self._delegate.stream(request, cancellation)

    def shutdown(self) -> None:
        self._delegate.shutdown()


class FaultInjectingToolExecutor:
    def __init__(self, delegate: Any, controller: FaultController) -> None:
        self._delegate = delegate
        self._controller = controller

    def execute(
        self,
        registered: RegisteredTool,
        request: ToolRequest,
        cancellation: CancellationToken | None = None,
    ) -> ToolResult:
        scenario = self._controller.trigger(FaultPoint.TOOL_EXECUTE, task_id=request.task_id)
        if scenario is None:
            return self._delegate.execute(registered, request, cancellation)
        if scenario.kind is FaultKind.TOOL_TIMEOUT:
            raise TaskTimeoutError(
                "injected tool timeout",
                details=_details(scenario, request.task_id),
            )
        if scenario.kind is FaultKind.MALFORMED_TOOL_CALL:
            malformed = replace(
                request,
                arguments={"relative_path": "README.md", "max_characters": "not-an-integer"},
            )
            return self._delegate.execute(registered, malformed, cancellation)
        result = self._delegate.execute(registered, request, cancellation)
        if scenario.kind is FaultKind.CORRUPTED_TOOL_RESULT:
            return replace(result, task_id=f"corrupted-{result.task_id}")
        return result


class FaultInjectingPersistence:
    def __init__(self, delegate: Any, controller: FaultController) -> None:
        self._delegate = delegate
        self._controller = controller

    def save_task_result(self, result: TaskResult) -> None:
        scenario = self._controller.trigger(
            FaultPoint.PERSISTENCE_SAVE_RESULT,
            task_id=result.task_id,
        )
        if scenario is not None and scenario.kind is FaultKind.DATABASE_RESULT_FAILURE:
            raise DatabaseOperationError(
                "injected database failure while saving terminal task output",
                details=_details(scenario, result.task_id),
            )
        self._delegate.save_task_result(result)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)
