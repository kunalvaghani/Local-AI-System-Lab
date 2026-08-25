"""Execute one armed deterministic fault scenario and classify its outcome."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from ..agents import TECHNICAL_EXPLAINER
from ..errors import LabError
from .models import ChaosScenarioResult, FaultKind, FaultScenario


EXPECTED: dict[FaultKind, tuple[str | None, str | None, bool]] = {
    FaultKind.MODEL_TIMEOUT: ("timeout", "task_timeout", True),
    FaultKind.INVALID_MODEL_OUTPUT: ("invalid_output", "invalid_output", True),
    FaultKind.CONTEXT_OVERFLOW: ("context_overflow", "context_overflow", True),
    FaultKind.SIMULATED_OOM: ("out_of_memory", "model_out_of_memory", True),
    FaultKind.TOOL_TIMEOUT: ("timeout", "task_timeout", True),
    FaultKind.CORRUPTED_TOOL_RESULT: ("invalid_output", "invalid_output", True),
    FaultKind.MALFORMED_TOOL_CALL: (
        "tool_failed",
        "tool_argument_validation_error",
        True,
    ),
    FaultKind.DATABASE_RESULT_FAILURE: (
        "completed",
        "database_operation_failed",
        False,
    ),
    FaultKind.AGENT_CRASH: ("completed", None, True),
}


def _trace_steps(runtime: Any, task_id: str | None) -> int:
    traces = runtime.components.traces
    if traces is None or task_id is None:
        return 0
    run = traces.for_task(task_id)
    return len(traces.steps(run.run_id))


def execute_fault_scenario(
    runtime: Any,
    scenario: FaultScenario,
    *,
    baseline_ms: float,
) -> ChaosScenarioResult:
    if scenario.kind is FaultKind.AGENT_CRASH:
        raise ValueError("agent crash requires the process-interruption runner")
    runtime.start()
    started = perf_counter()
    error: LabError | None = None
    result: Any = None
    try:
        if scenario.kind in {
            FaultKind.TOOL_TIMEOUT,
            FaultKind.CORRUPTED_TOOL_RESULT,
            FaultKind.MALFORMED_TOOL_CALL,
        }:
            result = runtime.run_tool(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                tool_name="project_context_read",
                arguments={"relative_path": "README.md", "max_characters": 80},
            )
        else:
            result = runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                objective=f"Controlled Stage 13 scenario: {scenario.scenario_id}",
            )
    except LabError as caught:
        error = caught
    finally:
        duration_ms = (perf_counter() - started) * 1000.0

    controller = runtime.components.faults
    records = tuple(controller.snapshot()) if controller is not None else tuple()
    task_id = records[-1].task_id if records else getattr(result, "task_id", None)
    actual_state = runtime.task_state(task_id).value if task_id is not None else None
    expected_state, expected_error, expected_containment = EXPECTED[scenario.kind]
    actual_error = error.code if error is not None else None
    matched = (
        len(records) == scenario.max_injections
        and actual_state == expected_state
        and actual_error == expected_error
    )
    contained = matched and expected_containment
    details = {
        "fault_records": [record.as_dict() for record in records],
        "error": error.as_dict() if error is not None else None,
        "state_history": (
            [item.to_state.value for item in runtime.state_history(task_id)]
            if task_id is not None
            else []
        ),
    }
    scenario_result = ChaosScenarioResult(
        scenario_id=scenario.scenario_id,
        kind=scenario.kind.value,
        target=scenario.point.value,
        task_id=task_id,
        expected_state=expected_state,
        actual_state=actual_state,
        expected_error_code=expected_error,
        actual_error_code=actual_error,
        injected=bool(records),
        injection_count=len(records),
        duration_ms=duration_ms,
        baseline_ms=baseline_ms,
        added_latency_ms=duration_ms - baseline_ms,
        recovery_attempted=False,
        recovery_succeeded=None,
        contained=contained,
        expected_outcome_met=matched,
        trace_steps=_trace_steps(runtime, task_id),
        details=details,
    )
    runtime.shutdown()
    return scenario_result
