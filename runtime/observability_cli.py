"""Generate Stage 12 live/recent machine-readable telemetry reports."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Sequence

from .agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from .errors import LabError
from .factory import build_stage12_stub_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 12 unified runtime observability and metrics reports."
    )
    parser.set_defaults(
        database=None,
        window_minutes=None,
        limit=None,
        event_limit=None,
        no_live=False,
    )
    subparsers = parser.add_subparsers(dest="command")
    demo = subparsers.add_parser(
        "demo",
        help="Create inference, tool, failure, and recovery evidence before reporting.",
    )
    _report_arguments(demo, database_required=False)
    report = subparsers.add_parser("report", help="Report an existing SQLite database.")
    _report_arguments(report, database_required=True)
    return parser


def _report_arguments(parser: argparse.ArgumentParser, *, database_required: bool) -> None:
    parser.add_argument("--database", required=database_required, default=None)
    parser.add_argument("--window-minutes", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None, help="Recent task limit.")
    parser.add_argument("--event-limit", type=int, default=None)
    parser.add_argument("--no-live", action="store_true")


def _report(runtime: object, args: argparse.Namespace) -> dict[str, object]:
    backend = runtime.components.observability  # type: ignore[attr-defined]
    if backend is None:
        raise RuntimeError("observability backend is not composed")
    return backend.report(
        window_minutes=args.window_minutes,
        recent_task_limit=args.limit,
        recent_event_limit=args.event_limit,
        include_live=not args.no_live,
    ).as_dict()


def _demo(database: Path, args: argparse.Namespace) -> dict[str, object]:
    runtime = build_stage12_stub_runtime(database)
    runtime.start()
    expected_failure: dict[str, object] | None = None
    try:
        inference = runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            objective="Produce deterministic observability evidence without a real model.",
        )
        tool = runtime.run_tool(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 80},
        )
        try:
            runtime.run_tool(
                agent_id=RISK_ANALYST.agent_id,
                tool_name="project_context_read",
                arguments={"relative_path": "README.md", "max_characters": 20},
            )
        except LabError as error:
            expected_failure = error.as_dict()
        prepared = runtime.prepare_recoverable_task(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            objective="Recover this observability demonstration task.",
        )
        recovered = runtime.recover_task(prepared.task_id)
        report = _report(runtime, args)
    finally:
        runtime.shutdown()
    return {
        "stage": 12,
        "purpose": "unify recent task, model, tool, scheduler, failure, recovery, inference, and hardware telemetry",
        "database": str(database),
        "demonstration": {
            "inference_task_id": inference.task_id,
            "tool_task_id": tool.task_id,
            "failed_operation": expected_failure,
            "recovered_task_id": recovered.task_id,
            "real_llm_calls": (
                inference.metadata.get("real_llm_calls", 0)
                + recovered.metadata.get("real_llm_calls", 0)
            ),
        },
        "report": report,
        "component_roles": {
            "sqlite_source": "queries durable tasks, events, outputs, tools, recoveries, and trace identities",
            "aggregator": "computes counts plus latency/resource distributions without fabricating missing samples",
            "scheduler_snapshot": "reports current queue, running work, outcomes, and wait percentiles",
            "hardware_snapshot": "reports source-labelled current CPU, RAM, GPU, and VRAM evidence",
            "cli": "emits one JSON report for controlled demonstration or an existing database",
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "demo"
    database = (
        Path(args.database).resolve()
        if args.database
        else (Path("data") / f"stage12-observability-{uuid.uuid4().hex}.db").resolve()
    )
    try:
        if command == "demo":
            payload = _demo(database, args)
        else:
            if not database.is_file():
                raise OSError(f"observability database does not exist: {database}")
            report_runtime = build_stage12_stub_runtime(database)
            payload = {
                "stage": 12,
                "purpose": "report recent persisted telemetry and optional live scheduler/hardware state",
                "database": str(database),
                "report": _report(report_runtime, args),
            }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except (LabError, OSError, RuntimeError, ValueError) as error:
        payload = error.as_dict() if isinstance(error, LabError) else {
            "code": "observability_command_failed",
            "message": str(error),
        }
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
