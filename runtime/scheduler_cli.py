"""Compare Stage 6 FIFO and priority execution order with controlled work."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import replace
from threading import Event
from time import perf_counter
from typing import Any

from .cancellation import CancellationToken
from .models import InferenceResult, Task
from .scheduler import (
    QueuedScheduler,
    SchedulerPolicy,
    SchedulingOptions,
    WorkloadClass,
)


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Demonstrate Stage 6 FIFO and priority request ordering.",
    )


def _task(label: str) -> Task:
    created = Task.create(agent_id="scheduler-demo", objective=f"Run {label}")
    return replace(created, task_id=label)


def _result(label: str) -> InferenceResult:
    return InferenceResult(
        text=label,
        model_id="controlled-stage-6-workload",
        backend_name="scheduler-demonstration",
        metadata={"real_llm_calls": 0},
    )


def _run_policy(policy: SchedulerPolicy) -> dict[str, Any]:
    scheduler = QueuedScheduler(policy=policy, max_workers=1)
    scheduler.start()
    blocker_started = Event()
    release = Event()
    started = perf_counter()

    def blocker(cancellation: CancellationToken) -> InferenceResult:
        blocker_started.set()
        release.wait(1)
        return _result("blocker")

    try:
        handles = [
            scheduler.submit(
                _task("blocker"),
                blocker,
                SchedulingOptions(timeout_ms=None),
            )
        ]
        if not blocker_started.wait(0.5):
            raise RuntimeError("scheduler demonstration blocker did not start")
        handles.extend(
            [
                scheduler.submit(
                    _task("background"),
                    lambda cancellation: _result("background"),
                    SchedulingOptions(
                        workload=WorkloadClass.BACKGROUND,
                        timeout_ms=1_000,
                    ),
                ),
                scheduler.submit(
                    _task("standard"),
                    lambda cancellation: _result("standard"),
                    SchedulingOptions(
                        workload=WorkloadClass.STANDARD,
                        timeout_ms=1_000,
                    ),
                ),
                scheduler.submit(
                    _task("interactive"),
                    lambda cancellation: _result("interactive"),
                    SchedulingOptions(
                        workload=WorkloadClass.INTERACTIVE,
                        timeout_ms=1_000,
                    ),
                ),
            ]
        )
        release.set()
        results = [handle.result(1) for handle in handles]
        metrics = scheduler.snapshot()
        return {
            "policy": policy.value,
            "queued_submission_order": ["background", "standard", "interactive"],
            "controlled_execution_order": list(metrics.execution_order[1:]),
            "outputs": [result.value.text for result in results[1:]],
            "wall_time_ms": (perf_counter() - started) * 1_000,
            "metrics": metrics.as_dict(),
        }
    finally:
        release.set()
        scheduler.shutdown()


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    fifo = _run_policy(SchedulerPolicy.FIFO)
    priority = _run_policy(SchedulerPolicy.PRIORITY)
    payload = {
        "stage": 6,
        "purpose": "visible control of queued inference request order",
        "comparison": {"fifo": fifo, "priority": priority},
        "expected": {
            "fifo": ["background", "standard", "interactive"],
            "priority": ["interactive", "standard", "background"],
        },
        "matches_expected": (
            fifo["controlled_execution_order"]
            == ["background", "standard", "interactive"]
            and priority["controlled_execution_order"]
            == ["interactive", "standard", "background"]
        ),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["matches_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
