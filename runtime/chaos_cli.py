"""Run explicitly armed Stage 13 fault-injection and recovery experiments."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence
from uuid import uuid4

from .agents import TECHNICAL_EXPLAINER
from .errors import ConfigurationError, LabError
from .factory import build_stage13_stub_runtime
from .faults import (
    ChaosReport,
    ChaosScenarioResult,
    EXPECTED,
    FaultKind,
    FaultPoint,
    FaultScenario,
    execute_fault_scenario,
    load_chaos_config,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 13 deterministic and bounded local chaos experiments."
    )
    parser.add_argument("--database", default=None)
    parser.add_argument("--config", default="configs/chaos.json")
    parser.add_argument("--scenario", action="append", default=None)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Explicitly arm the selected fault scenarios.",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scenario-id", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--hold-seconds", type=float, default=120.0, help=argparse.SUPPRESS)
    return parser


def _build(
    database: Path,
    config: str,
    *,
    armed: bool,
    scenario_ids: tuple[str, ...],
) -> Any:
    return build_stage13_stub_runtime(
        database,
        chaos_config_path=config,
        arm_faults=armed,
        scenario_ids=scenario_ids,
    )


def _baseline(database: Path, config: str) -> tuple[dict[str, float], int]:
    runtime = _build(database, config, armed=False, scenario_ids=tuple())
    runtime.start()
    real_calls = 0
    try:
        started = perf_counter()
        inference = runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            objective="Stage 13 no-fault inference baseline.",
        )
        inference_ms = (perf_counter() - started) * 1000.0
        started = perf_counter()
        runtime.run_tool(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 80},
        )
        tool_ms = (perf_counter() - started) * 1000.0
        real_calls += int(inference.metadata.get("real_llm_calls", 0))
    finally:
        runtime.shutdown()
    return {"inference": inference_ms, "tool": tool_ms}, real_calls


def _crash_worker(database: Path, config: str, scenario_id: str, hold_seconds: float) -> int:
    runtime = _build(database, config, armed=True, scenario_ids=(scenario_id,))
    runtime.start()
    task = runtime.prepare_recoverable_task(
        agent_id=TECHNICAL_EXPLAINER.agent_id,
        objective="Recover this Stage 13 chaos task after process termination.",
        input_data={"chaos_scenario": scenario_id},
    )
    controller = runtime.components.faults
    if controller is None:
        raise RuntimeError("fault controller is not composed")
    scenario = controller.trigger(FaultPoint.RECOVERY_CHECKPOINT, task_id=task.task_id)  # type: ignore[attr-defined]
    if scenario is None:
        raise RuntimeError("agent crash fault did not arm")
    candidate = runtime.components.persistence.recovery_candidate(task.task_id)  # type: ignore[union-attr]
    print(
        json.dumps(
            {
                "task_id": task.task_id,
                "process_id": os.getpid(),
                "state": runtime.task_state(task.task_id).value,
                "candidate": candidate.as_dict(),
                "fault_records": [item.as_dict() for item in controller.snapshot()],
            },
            sort_keys=True,
        ),
        flush=True,
    )
    time.sleep(hold_seconds)
    return 2


def _trace_steps(runtime: Any, task_id: str) -> int:
    run = runtime.components.traces.for_task(task_id)
    return len(runtime.components.traces.steps(run.run_id))


def _agent_crash(
    database: Path,
    config: str,
    scenario: FaultScenario,
    baseline_ms: float,
) -> ChaosScenarioResult:
    started = perf_counter()
    command = [
        sys.executable,
        "-m",
        "runtime.chaos_cli",
        "--worker",
        "--database",
        str(database),
        "--config",
        config,
        "--scenario-id",
        scenario.scenario_id,
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path.cwd(),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        if process.stdout is None:
            raise RuntimeError("chaos worker stdout is unavailable")
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"chaos worker did not report its checkpoint: {stderr}")
        before = json.loads(line)
        process.terminate()
        exit_code = process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    restarted = _build(database, config, armed=False, scenario_ids=tuple())
    restarted.start()
    try:
        candidate = restarted.components.persistence.recovery_candidate(before["task_id"])  # type: ignore[union-attr]
        result = restarted.recover_task(before["task_id"])
        actual_state = result.final_state.value if result.final_state is not None else None
        trace_steps = _trace_steps(restarted, before["task_id"])
        real_calls = int(result.metadata.get("real_llm_calls", 0))
    finally:
        restarted.shutdown()
    duration_ms = (perf_counter() - started) * 1000.0
    expected_state, expected_error, _ = EXPECTED[scenario.kind]
    matched = (
        exit_code != 0
        and actual_state == expected_state
        and expected_error is None
        and candidate.disposition.value == "recoverable"
    )
    return ChaosScenarioResult(
        scenario_id=scenario.scenario_id,
        kind=scenario.kind.value,
        target=scenario.point.value,
        task_id=before["task_id"],
        expected_state=expected_state,
        actual_state=actual_state,
        expected_error_code=expected_error,
        actual_error_code=None,
        injected=True,
        injection_count=len(before["fault_records"]),
        duration_ms=duration_ms,
        baseline_ms=baseline_ms,
        added_latency_ms=duration_ms - baseline_ms,
        recovery_attempted=True,
        recovery_succeeded=actual_state == "completed",
        contained=matched,
        expected_outcome_met=matched,
        trace_steps=trace_steps,
        details={
            "worker_process_id": before["process_id"],
            "worker_exit_code": exit_code,
            "state_before_termination": before["state"],
            "checkpoint": before["candidate"]["checkpoint"],
            "fault_records": before["fault_records"],
            "state_history": [item.to_state.value for item in result.state_history],
            "real_llm_calls": real_calls,
        },
    )


def _run(database: Path, config_path: str, selected: tuple[str, ...] | None) -> dict[str, Any]:
    config = load_chaos_config(config_path)
    plan = config.plan(armed=True, scenario_ids=selected)
    if not plan.scenarios:
        raise ConfigurationError("at least one chaos scenario must be selected")
    started_at = datetime.now(timezone.utc)
    baselines, real_calls = _baseline(database, config_path)
    results: list[ChaosScenarioResult] = []
    for scenario in plan.scenarios:
        if scenario.kind is FaultKind.AGENT_CRASH:
            result = _agent_crash(
                database,
                config_path,
                scenario,
                baselines["inference"],
            )
        else:
            runtime = _build(
                database,
                config_path,
                armed=True,
                scenario_ids=(scenario.scenario_id,),
            )
            baseline = (
                baselines["tool"]
                if scenario.point is FaultPoint.TOOL_EXECUTE
                else baselines["inference"]
            )
            result = execute_fault_scenario(runtime, scenario, baseline_ms=baseline)
        results.append(result)
        real_calls += int(result.details.get("real_llm_calls", 0))

    reporting = _build(database, config_path, armed=False, scenario_ids=tuple())
    observability = reporting.components.observability.report(include_live=False).as_dict()  # type: ignore[union-attr]
    integrity = reporting.components.persistence.integrity_check()  # type: ignore[union-attr]
    report = ChaosReport(
        run_id=str(uuid4()),
        database=str(database),
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        baselines_ms=baselines,
        scenarios=tuple(results),
        observability={
            "collection_ms": observability["collection_ms"],
            "totals": observability["totals"],
            "task_states": observability["task_states"],
            "warnings": observability["warnings"],
        },
        database_integrity=integrity,
        real_llm_calls=real_calls,
    )
    payload = report.as_dict()
    payload["component_roles"] = {
        "fault_plan": "strictly validates bounded deterministic scenarios and remains disabled by default",
        "controller": "arms explicit points, enforces injection counts, delays, and records fault.injected metrics",
        "adapters": "inject typed failures or corruption at inference, tool, and persistence protocols",
        "process_harness": "terminates a checkpointed worker and restarts recovery against the same SQLite database",
        "chaos_report": "compares expected/actual state and error, latency, containment, recovery, traces, and observability",
    }
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    database = (
        Path(args.database).resolve()
        if args.database
        else (Path("data") / f"stage13-chaos-{uuid4().hex}.db").resolve()
    )
    try:
        if args.worker:
            if not args.scenario_id:
                raise ConfigurationError("chaos worker requires --scenario-id")
            return _crash_worker(
                database,
                args.config,
                args.scenario_id,
                args.hold_seconds,
            )
        if not args.execute:
            raise ConfigurationError(
                "fault injection is disabled; pass --execute to arm the selected scenarios"
            )
        selected = tuple(args.scenario) if args.scenario else None
        print(json.dumps(_run(database, args.config, selected), indent=2, sort_keys=True))
        return 0
    except (LabError, OSError, RuntimeError, ValueError) as error:
        payload = error.as_dict() if isinstance(error, LabError) else {
            "code": "chaos_command_failed",
            "message": str(error),
        }
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
