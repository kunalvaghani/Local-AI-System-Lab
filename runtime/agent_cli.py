"""Run specialized agents through the current validated local runtime."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from .agents import stage3_agents
from .errors import LabError, ValidationError
from .factory import build_stage11_runtime
from .models import LifecycleEvent, TaskResult
from .scheduler import SchedulingOptions, WorkloadClass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute specialized agents through the Stage 11 traceable runtime.",
    )
    parser.add_argument(
        "--config",
        default="configs/inference-baseline.json",
        help="Pinned Stage 2 llama.cpp/GGUF configuration.",
    )
    parser.add_argument(
        "--workload",
        choices=[workload.value for workload in WorkloadClass],
        default=WorkloadClass.STANDARD.value,
        help="Workload class used by adaptive profile selection and scheduling.",
    )
    parser.add_argument(
        "--database",
        default=None,
        help="Override the ignored Stage 11 SQLite database path.",
    )
    parser.add_argument(
        "--agent",
        action="append",
        choices=[agent.agent_id for agent in stage3_agents()],
        help="Agent to run; repeat for both. The default runs both agents.",
    )
    parser.add_argument(
        "--objective",
        default=None,
        help="Override the objective when exactly one agent is selected.",
    )
    return parser


def _result_payload(result: TaskResult) -> dict[str, Any]:
    return {
        "agent_id": result.agent_id,
        "task_id": result.task_id,
        "objective": result.objective,
        "state": result.final_state.value if result.final_state else None,
        "model": result.model_id,
        "backend": result.backend_name,
        "output": result.output,
        "metadata": result.metadata,
        "metrics": (
            result.inference_metrics.as_dict()
            if result.inference_metrics is not None
            else None
        ),
        "state_history": [
            {
                "sequence": transition.sequence,
                "from_state": (
                    transition.from_state.value
                    if transition.from_state is not None
                    else None
                ),
                "to_state": transition.to_state.value,
                "reason": transition.reason,
                "recorded_at_utc": transition.recorded_at.isoformat(),
            }
            for transition in result.state_history
        ],
    }


def _event_payload(event: LifecycleEvent) -> dict[str, Any]:
    return {
        "event": event.name,
        "recorded_at_utc": event.recorded_at.isoformat(),
        "agent_id": event.agent_id,
        "task_id": event.task_id,
        "state": event.state.value if event.state else None,
        "data": event.data,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    selected = args.agent or [agent.agent_id for agent in stage3_agents()]
    runtime = None
    results: list[TaskResult] = []
    try:
        if args.objective is not None and len(selected) != 1:
            raise ValidationError(
                "--objective requires exactly one selected agent"
            )
        runtime = build_stage11_runtime(
            inference_config_path=args.config,
            database_path=args.database,
        )
        runtime.start()
        for agent_id in selected:
            results.append(
                runtime.run(
                    agent_id=agent_id,
                    objective=args.objective,
                    scheduling=SchedulingOptions(
                        workload=WorkloadClass(args.workload)
                    ),
                )
            )
        runtime.shutdown()
        print(
            json.dumps(
                {
                    "stage": 11,
                    "purpose": "durable local-agent execution with hash-chained traces and bounded replay",
                    "agents": [_result_payload(result) for result in results],
                    "lifecycle_events": [
                        _event_payload(event)
                        for result in results
                        for event in runtime.components.events.snapshot(result.task_id)
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except LabError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if runtime is not None and runtime.status.value != "stopped":
            runtime.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
