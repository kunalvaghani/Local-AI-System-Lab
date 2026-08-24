"""Stage 10 process-interruption and SQLite recovery demonstration."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from .agents import TECHNICAL_EXPLAINER
from .factory import build_stage10_stub_runtime


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interrupt a checkpointed process and recover it after restart.",
    )
    parser.add_argument("--db", default=None, help="SQLite database path; defaults to a unique ignored data file.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--hold-seconds", type=float, default=120.0, help=argparse.SUPPRESS)
    return parser


def _worker(database_path: Path, hold_seconds: float) -> int:
    runtime = build_stage10_stub_runtime(database_path)
    runtime.start()
    task = runtime.prepare_recoverable_task(
        agent_id=TECHNICAL_EXPLAINER.agent_id,
        objective="Recover this local task after the worker process is interrupted.",
        input_data={"demo": "stage10-process-interruption"},
    )
    candidate = runtime.components.persistence.recovery_candidate(task.task_id)  # type: ignore[union-attr]
    print(
        json.dumps(
            {
                "task_id": task.task_id,
                "process_id": os.getpid(),
                "state": runtime.task_state(task.task_id).value,
                "candidate": candidate.as_dict(),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    time.sleep(hold_seconds)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    database_path = (
        Path(args.db).resolve()
        if args.db
        else (Path("data") / f"stage10-recovery-{uuid4().hex}.db").resolve()
    )
    if args.worker:
        return _worker(database_path, args.hold_seconds)

    command = [
        sys.executable,
        "-m",
        "runtime.recovery_cli",
        "--worker",
        "--db",
        str(database_path),
    ]
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path.cwd(),
        creationflags=creationflags,
    )
    try:
        if process.stdout is None:
            raise RuntimeError("recovery worker stdout is unavailable")
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"recovery worker did not report its checkpoint: {stderr}")
        before = json.loads(line)
        process.terminate()
        interrupted_exit_code = process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    restarted = build_stage10_stub_runtime(database_path)
    restarted.start()
    try:
        persistence = restarted.components.persistence
        candidate = persistence.recovery_candidate(before["task_id"])  # type: ignore[union-attr]
        result = restarted.recover_task(before["task_id"])
        counts = persistence.table_counts()  # type: ignore[union-attr]
        integrity = persistence.integrity_check()  # type: ignore[union-attr]
        events = [
            event.name
            for event in restarted.components.events.snapshot(before["task_id"])
        ]
    finally:
        restarted.shutdown()

    print(
        json.dumps(
            {
                "stage": 10,
                "purpose": "persist runtime state and recover safely after process interruption",
                "database": str(database_path),
                "interruption": {
                    "worker_process_id": before["process_id"],
                    "exit_code": interrupted_exit_code,
                    "state_before_kill": before["state"],
                    "durable_checkpoint": before["candidate"]["checkpoint"],
                },
                "restart": {
                    "candidate": candidate.as_dict(),
                    "final_state": result.final_state.value if result.final_state else None,
                    "state_history": [item.to_state.value for item in result.state_history],
                    "output": result.output,
                    "real_llm_calls": result.metadata.get("real_llm_calls"),
                    "events": events,
                },
                "database_evidence": {
                    "schema_version": persistence.schema_version,  # type: ignore[union-attr]
                    "integrity_check": integrity,
                    "table_counts": counts,
                },
                "recovery_boundary": "Only recovery_ready PLANNING checkpoints before model/tool invocation are retried; terminal or in-flight side-effect boundaries are not.",
                "component_roles": {
                    "sqlite_store": "persists agents, tasks, states, checkpoints, events, metrics, steps, model configuration, tools, outputs, and recovery attempts",
                    "recovery_checkpoint": "marks a committed pre-invocation point safe to retry",
                    "recovering_state": "records restart ownership before normal planning resumes",
                    "recovery_ledger": "records the attempt and outcome without deleting prior history",
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
