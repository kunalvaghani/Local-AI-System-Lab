"""Thread-safe, count-bounded and source-recorded fault activation."""

from __future__ import annotations

from threading import Lock
from time import sleep
from typing import Any

from ..models import MetricEvent, utc_now
from .models import FaultPlan, FaultPoint, FaultRecord, FaultScenario


class FaultController:
    def __init__(self, plan: FaultPlan, metrics: Any) -> None:
        self.plan = plan
        self._metrics = metrics
        self._counts: dict[str, int] = {}
        self._records: list[FaultRecord] = []
        self._lock = Lock()

    @property
    def armed(self) -> bool:
        return self.plan.armed

    def trigger(self, point: FaultPoint, *, task_id: str | None) -> FaultScenario | None:
        if not self.plan.armed:
            return None
        with self._lock:
            scenario = next(
                (
                    item
                    for item in self.plan.scenarios
                    if item.point is point
                    and self._counts.get(item.scenario_id, 0) < item.max_injections
                ),
                None,
            )
            if scenario is None:
                return None
            occurrence = self._counts.get(scenario.scenario_id, 0) + 1
            self._counts[scenario.scenario_id] = occurrence
            record = FaultRecord(
                scenario_id=scenario.scenario_id,
                kind=scenario.kind,
                point=point,
                occurrence=occurrence,
                task_id=task_id,
                injected_at=utc_now(),
                delay_ms=scenario.delay_ms,
            )
            self._records.append(record)
        self._metrics.record(
            MetricEvent(
                name="fault.injected",
                task_id=task_id,
                attributes=record.as_dict(),
            )
        )
        if scenario.delay_ms:
            sleep(scenario.delay_ms / 1000.0)
        return scenario

    def snapshot(self) -> tuple[FaultRecord, ...]:
        with self._lock:
            return tuple(self._records)
