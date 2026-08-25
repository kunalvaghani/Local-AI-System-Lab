"""Unified Stage 12 aggregation over durable and live runtime evidence."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from time import perf_counter
from typing import Any, Protocol

from ..errors import ValidationError
from ..models import utc_now
from .config import ObservabilityConfig
from .models import MetricDistribution, ObservabilityReport, TaskTelemetry


class ObservabilitySource(Protocol):
    def query(
        self,
        *,
        since: datetime,
        recent_task_limit: int,
        recent_event_limit: int,
    ) -> dict[str, Any]: ...


class SnapshotProvider(Protocol):
    def snapshot(self) -> Any: ...


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def distribution(values: Sequence[float | int | None], unit: str) -> MetricDistribution:
    samples = [float(value) for value in values if value is not None and not isinstance(value, bool)]
    if not samples:
        return MetricDistribution(0, None, None, None, None, None, unit)
    return MetricDistribution(
        count=len(samples),
        minimum=min(samples),
        p50=_percentile(samples, 0.50),
        p95=_percentile(samples, 0.95),
        maximum=max(samples),
        mean=sum(samples) / len(samples),
        unit=unit,
    )


class UnifiedObservabilityBackend:
    """Build recent and live machine-readable telemetry without inventing values."""

    def __init__(
        self,
        source: ObservabilitySource,
        scheduler: SnapshotProvider,
        hardware: SnapshotProvider | None,
        config: ObservabilityConfig,
    ) -> None:
        self._source = source
        self._scheduler = scheduler
        self._hardware = hardware
        self._config = config

    def report(
        self,
        *,
        window_minutes: int | None = None,
        recent_task_limit: int | None = None,
        recent_event_limit: int | None = None,
        include_live: bool = True,
    ) -> ObservabilityReport:
        resolved_window = (
            self._config.default_window_minutes
            if window_minutes is None
            else window_minutes
        )
        resolved_task_limit = (
            self._config.recent_task_limit
            if recent_task_limit is None
            else recent_task_limit
        )
        resolved_event_limit = (
            self._config.recent_event_limit
            if recent_event_limit is None
            else recent_event_limit
        )
        for name, value in (
            ("window_minutes", resolved_window),
            ("recent_task_limit", resolved_task_limit),
            ("recent_event_limit", resolved_event_limit),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValidationError(f"observability {name} must be a positive integer")
        if not isinstance(include_live, bool):
            raise ValidationError("observability include_live must be boolean")

        collection_started = perf_counter()
        ended_at = utc_now()
        started_at = ended_at - timedelta(minutes=resolved_window)
        raw = self._source.query(
            since=started_at,
            recent_task_limit=resolved_task_limit,
            recent_event_limit=resolved_event_limit,
        )
        warnings: list[str] = []
        live_scheduler = None
        live_hardware = None
        if include_live:
            try:
                snapshot = self._scheduler.snapshot()
                live_scheduler = snapshot.as_dict()
            except Exception as error:
                warnings.append(f"live scheduler snapshot unavailable: {type(error).__name__}")
            if self._config.include_live_hardware and self._hardware is not None:
                try:
                    snapshot = self._hardware.snapshot()
                    live_hardware = snapshot.as_dict()
                    warnings.extend(str(item) for item in live_hardware.get("warnings", []))
                except Exception as error:
                    warnings.append(f"live hardware snapshot unavailable: {type(error).__name__}")
            elif self._config.include_live_hardware:
                warnings.append("live hardware profiler is not configured")

        tasks = tuple(self._task(item) for item in raw["recent_tasks"])
        event_counts = raw["event_counts"]
        recoveries = raw["recoveries"]
        recovery_statuses: dict[str, int] = {}
        for recovery in recoveries:
            status = str(recovery["status"])
            recovery_statuses[status] = recovery_statuses.get(status, 0) + 1
        completed = int(raw["task_states"].get("completed", 0))
        failures = int(event_counts.get("task.failed", 0))
        totals: dict[str, Any] = {
            "tasks": int(raw["task_total"]),
            "completed_tasks": completed,
            "failed_tasks": failures,
            "completion_rate_percent": (
                completed / int(raw["task_total"]) * 100.0
                if raw["task_total"]
                else None
            ),
            "model_calls_started": int(event_counts.get("model.invocation.started", 0)),
            "model_calls_completed": int(event_counts.get("model.invocation.completed", 0)),
            "tool_calls": int(raw["tool_count"]),
            "router_decisions": int(event_counts.get("route.selected", 0)),
            "recoveries": len(recoveries),
            "retries": len(recoveries),
            "recovery_statuses": dict(sorted(recovery_statuses.items())),
            "trace_runs": int(raw["trace_run_count"]),
            "trace_steps": int(raw["trace_step_count"]),
            "replay_reports": int(raw["replay_count"]),
            "fault_injections": int(event_counts.get("fault.injected", 0)),
        }

        outputs = raw["aggregate_outputs"]
        inference_metrics = [item["payload"].get("metrics") or {} for item in outputs]
        scheduler_samples = [item["attributes"] for item in raw["scheduler_samples"]]
        distributions = {
            "task_duration_ms": distribution(
                [
                    (_datetime(item["updated_at_utc"]) - _datetime(item["created_at_utc"])).total_seconds() * 1000.0
                    for item in raw["task_durations"]
                ],
                "ms",
            ),
            "queue_wait_ms": distribution(
                [_number(item.get("queue_wait_ms")) for item in scheduler_samples],
                "ms",
            ),
            "scheduler_execution_ms": distribution(
                [_number(item.get("execution_ms")) for item in scheduler_samples],
                "ms",
            ),
            "tool_latency_ms": distribution(
                [
                    (
                        (_datetime(item["finished_at_utc"]) - _datetime(item["started_at_utc"])).total_seconds() * 1000.0
                        if item["finished_at_utc"] is not None
                        else None
                    )
                    for item in raw["tool_samples"]
                ],
                "ms",
            ),
            "recovery_latency_ms": distribution(
                [
                    (
                        (_datetime(item["finished_at_utc"]) - _datetime(item["started_at_utc"])).total_seconds() * 1000.0
                        if item["finished_at_utc"] is not None
                        else None
                    )
                    for item in recoveries
                ],
                "ms",
            ),
            "inference_total_ms": distribution(
                [_number(item.get("total_ms")) for item in inference_metrics],
                "ms",
            ),
            "ttft_ms": distribution(
                [_number(item.get("ttft_ms")) for item in inference_metrics],
                "ms",
            ),
            "generation_tokens_per_second": distribution(
                [_number(item.get("tokens_per_second")) for item in inference_metrics],
                "tokens/s",
            ),
            "peak_process_ram_mib": distribution(
                [_number(item.get("peak_process_ram_mib")) for item in inference_metrics],
                "MiB",
            ),
            "vram_delta_mib": distribution(
                [_number(item.get("vram_delta_mib")) for item in inference_metrics],
                "MiB",
            ),
        }
        collection_ms = (perf_counter() - collection_started) * 1000.0
        return ObservabilityReport(
            generated_at=utc_now(),
            window_started_at=started_at,
            window_ended_at=ended_at,
            collection_ms=collection_ms,
            totals=totals,
            task_states=raw["task_states"],
            distributions=distributions,
            live_scheduler=live_scheduler,
            live_hardware=live_hardware,
            recent_tasks=tasks,
            recent_events=tuple(raw["recent_events"]),
            sources={
                "task_state": "SQLite tasks/state_transitions",
                "activity_counts": "SQLite metric_events/tool_calls/recovery_attempts",
                "latency_and_inference": "SQLite outputs plus scheduler/tool/recovery timestamps",
                "traces": "SQLite trace_runs/trace_steps/trace_replays",
                "live_scheduler": "scheduler.snapshot()",
                "live_hardware": "hardware_profiler.snapshot()",
                "retries": "recovery_attempts; no independent generic retry subsystem exists",
            },
            warnings=tuple(dict.fromkeys(warnings)),
        )

    @staticmethod
    def _task(item: dict[str, Any]) -> TaskTelemetry:
        row = item["task"]
        output = json.loads(row["output_json"]) if row.get("output_json") else {}
        metadata = output.get("metadata") or {}
        events = item["events"]
        scheduler_event = next(
            (event for event in reversed(events) if event["name"] == "scheduler.request.completed"),
            None,
        )
        failure_event = next(
            (event for event in reversed(events) if event["name"] == "task.failed"),
            None,
        )
        hardware = None
        profile_selection = metadata.get("profile_selection") or {}
        route = metadata.get("route") or {}
        if isinstance(profile_selection, dict):
            hardware = profile_selection.get("hardware")
        if hardware is None and isinstance(route, dict):
            evidence = route.get("evidence") or {}
            if isinstance(evidence, dict):
                hardware = evidence.get("hardware")
        created = _datetime(row["created_at_utc"])
        updated = _datetime(row["updated_at_utc"])
        return TaskTelemetry(
            task_id=row["task_id"],
            run_id=row.get("run_id"),
            agent_id=row["agent_id"],
            state=row.get("current_state"),
            created_at=created,
            updated_at=updated,
            duration_ms=(updated - created).total_seconds() * 1000.0,
            model_id=output.get("model_id") or row.get("trace_model_id"),
            output_type=row.get("output_type"),
            model_calls=sum(event["name"] == "model.invocation.started" for event in events),
            tool_calls=len(item["tools"]),
            router_decisions=sum(event["name"] == "route.selected" for event in events),
            recovery_attempts=len(item["recoveries"]),
            trace_steps=int(row.get("trace_step_count") or 0),
            queue_wait_ms=(
                _number(scheduler_event["attributes"].get("queue_wait_ms"))
                if scheduler_event
                else None
            ),
            scheduler_execution_ms=(
                _number(scheduler_event["attributes"].get("execution_ms"))
                if scheduler_event
                else None
            ),
            inference_metrics=output.get("metrics"),
            route_reason=metadata.get("route_reason"),
            hardware=hardware,
            failure=(
                {
                    "error_code": failure_event["attributes"].get("error_code"),
                    "error_details": failure_event["attributes"].get("error_details", {}),
                }
                if failure_event
                else None
            ),
        )
