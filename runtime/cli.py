"""Developer CLI demonstrating the Stage 1 lifecycle."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from .errors import LabError
from .factory import build_stage1_runtime
from .models import Agent


def _emit(event: str, **fields: Any) -> None:
    print(json.dumps({"event": event, **fields}, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Stage 1 lifecycle with deterministic stub inference.",
    )
    parser.add_argument(
        "--objective",
        default="Demonstrate the minimal local runtime lifecycle",
        help="Objective passed to the stub backend; no LLM is called.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = build_stage1_runtime()
    agent = Agent(
        agent_id="stage-1-demo-agent",
        name="Stage 1 Demo Agent",
        objective="Demonstrate component composition without real inference",
    )

    started = False
    try:
        runtime.start()
        started = True
        _emit("runtime.started", status=runtime.status.value)

        task = runtime.create_task(agent=agent, objective=args.objective)
        _emit("task.created", task_id=task.task_id)

        result = runtime.execute_task(task=task, agent=agent)
        _emit(
            "task.completed",
            task_id=result.task_id,
            output=result.output,
            backend=result.backend_name,
            model=result.model_id,
            real_llm_calls=result.metadata["real_llm_calls"],
        )
        return 0
    except LabError as error:
        print(json.dumps({"event": "runtime.error", **error.as_dict()}), file=sys.stderr)
        return 1
    finally:
        if started:
            runtime.shutdown()
            _emit("runtime.stopped", status=runtime.status.value)
