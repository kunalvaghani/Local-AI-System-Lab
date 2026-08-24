"""Inspect, replay, compare, and demonstrate Stage 11 execution traces."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

from .agents import TECHNICAL_EXPLAINER
from .errors import LabError
from .factory import build_stage11_stub_runtime
from .persistence import SQLiteRuntimeStore, load_persistence_config
from .tracing import SQLiteTraceStore, TraceReplayEngine, compare_traces


def _open_trace_store(database_path: str | Path) -> tuple[SQLiteRuntimeStore, SQLiteTraceStore]:
    config = replace(
        load_persistence_config(),
        database_path=Path(database_path).resolve(),
    )
    persistence = SQLiteRuntimeStore(config)
    return persistence, SQLiteTraceStore(persistence)


def _run_summary(run: Any, steps: Sequence[Any]) -> dict[str, Any]:
    determinism = Counter(step.determinism.value for step in steps)
    return {
        **run.as_dict(),
        "step_count": len(steps),
        "determinism_counts": dict(sorted(determinism.items())),
        "steps": [step.as_dict(include_payloads=False) for step in steps],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 11 hash-chained execution trace and deterministic replay tools."
    )
    subparsers = parser.add_subparsers(dest="command")
    parser.set_defaults(
        database=None,
        objective="Explain why deterministic replay must classify model generation separately.",
    )

    demo = subparsers.add_parser("demo", help="Run two deterministic stub tasks, replay, and compare them.")
    demo.add_argument("--database", default=None)
    demo.add_argument("--objective", default="Explain why deterministic replay must classify model generation separately.")

    inspect = subparsers.add_parser("inspect", help="Load a persisted trace.")
    inspect.add_argument("--database", required=True)
    identity = inspect.add_mutually_exclusive_group(required=True)
    identity.add_argument("--run-id")
    identity.add_argument("--task-id")

    replay = subparsers.add_parser("replay", help="Replay deterministic reducers without repeating side effects.")
    replay.add_argument("--database", required=True)
    replay.add_argument("--run-id", required=True)

    compare = subparsers.add_parser("compare", help="Compare semantic hashes across two runs.")
    compare.add_argument("--database", required=True)
    compare.add_argument("--left-run-id", required=True)
    compare.add_argument("--right-run-id", required=True)
    return parser


def _demo(database_path: str | Path, objective: str) -> dict[str, Any]:
    task_ids: list[str] = []
    for _ in range(2):
        runtime = build_stage11_stub_runtime(database_path)
        runtime.start()
        try:
            result = runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                objective=objective,
            )
            task_ids.append(result.task_id)
        finally:
            runtime.shutdown()

    persistence, traces = _open_trace_store(database_path)
    runs = [traces.for_task(task_id) for task_id in task_ids]
    run_steps = [tuple(traces.steps(run.run_id)) for run in runs]
    replay = TraceReplayEngine(traces).replay(runs[0].run_id)
    comparison = compare_traces(runs[0], run_steps[0], runs[1], run_steps[1])
    return {
        "stage": 11,
        "purpose": "inspect hash-chained evidence, replay deterministic reducers, and isolate nondeterministic generation",
        "database": str(Path(database_path).resolve()),
        "schema_version": persistence.schema_version,
        "integrity_check": persistence.integrity_check(),
        "runs": [
            _run_summary(run, steps) for run, steps in zip(runs, run_steps)
        ],
        "replay": replay.as_dict(),
        "comparison": comparison.as_dict(),
        "table_counts": persistence.table_counts(),
        "replay_boundary": "Deterministic reducers are verified; model generation, environmental observations, and tool side effects are never re-executed.",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "demo"
    try:
        if command == "demo":
            database = args.database or Path("data") / f"stage11-trace-{uuid.uuid4()}.db"
            payload = _demo(database, args.objective)
        elif command == "inspect":
            persistence, traces = _open_trace_store(args.database)
            run = traces.load_run(args.run_id) if args.run_id else traces.for_task(args.task_id)
            payload = {
                "stage": 11,
                "schema_version": persistence.schema_version,
                "integrity_check": persistence.integrity_check(),
                "trace": _run_summary(run, traces.steps(run.run_id)),
            }
        elif command == "replay":
            persistence, traces = _open_trace_store(args.database)
            payload = {
                "stage": 11,
                "integrity_check": persistence.integrity_check(),
                "replay": TraceReplayEngine(traces).replay(args.run_id).as_dict(),
            }
        else:
            persistence, traces = _open_trace_store(args.database)
            left = traces.load_run(args.left_run_id)
            right = traces.load_run(args.right_run_id)
            payload = {
                "stage": 11,
                "integrity_check": persistence.integrity_check(),
                "comparison": compare_traces(
                    left,
                    traces.steps(left.run_id),
                    right,
                    traces.steps(right.run_id),
                ).as_dict(),
            }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (LabError, OSError, ValueError) as error:
        if isinstance(error, LabError):
            payload = error.as_dict()
        else:
            payload = {"code": "trace_command_failed", "message": str(error)}
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
