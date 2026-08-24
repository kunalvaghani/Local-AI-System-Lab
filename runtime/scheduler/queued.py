"""Thread-safe FIFO/priority scheduler with bounded workers and aging."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from math import ceil
from queue import Empty, Queue
from threading import Condition, Event, Thread
from time import perf_counter
from uuid import uuid4

from ..cancellation import CancellationToken
from ..errors import (
    LabError,
    InferenceCancelledError,
    SchedulerCancelledError,
    SchedulerLifecycleError,
    TaskTimeoutError,
    ValidationError,
)
from ..models import InferenceResult, Task, utc_now
from .models import (
    ScheduledExecutionResult,
    SchedulerMetrics,
    SchedulerPolicy,
    SchedulerRequestSnapshot,
    SchedulerRequestStatus,
    SchedulingOptions,
)


ScheduledOperation = Callable[[CancellationToken], InferenceResult]


@dataclass(slots=True)
class _RequestRecord:
    request_id: str
    task: Task
    sequence: int
    operation: ScheduledOperation
    options: SchedulingOptions
    token: CancellationToken
    submitted_at: datetime
    submitted_monotonic: float
    queue_position_at_submit: int
    status: SchedulerRequestStatus = SchedulerRequestStatus.QUEUED
    effective_priority: int = 0
    started_at: datetime | None = None
    started_monotonic: float | None = None
    finished_at: datetime | None = None
    queue_wait_ms: float | None = None
    execution_ms: float | None = None
    value: InferenceResult | None = None
    error: BaseException | None = None
    completion: Event = field(default_factory=Event)


class ScheduledRequestHandle:
    """Caller-facing control for one submitted request."""

    def __init__(self, scheduler: "QueuedScheduler", record: _RequestRecord) -> None:
        self._scheduler = scheduler
        self._record = record

    @property
    def request_id(self) -> str:
        return self._record.request_id

    @property
    def task_id(self) -> str:
        return self._record.task.task_id

    def cancel(self) -> bool:
        return self._scheduler.cancel(self.request_id)

    def result(self, timeout: float | None = None) -> ScheduledExecutionResult:
        if not self._record.completion.wait(timeout):
            raise TaskTimeoutError(
                "caller stopped waiting for the scheduler result",
                details={
                    "request_id": self.request_id,
                    "scope": "caller_wait",
                },
            )
        if self._record.error is not None:
            raise self._record.error
        if self._record.value is None:
            raise SchedulerLifecycleError(
                "scheduler completed a request without a result or error",
                details={"request_id": self.request_id},
            )
        return ScheduledExecutionResult(
            value=self._record.value,
            request=self._scheduler.request_snapshot(self.request_id),
        )


class QueuedScheduler:
    """Bounded process-local scheduler supporting FIFO and aged priority."""

    def __init__(
        self,
        *,
        policy: SchedulerPolicy = SchedulerPolicy.PRIORITY,
        max_workers: int = 1,
        aging_interval_ms: int = 250,
        aging_increment: int = 5,
        starvation_threshold_ms: int = 5_000,
    ) -> None:
        if not isinstance(policy, SchedulerPolicy):
            raise ValidationError("scheduler policy must be a SchedulerPolicy")
        if isinstance(max_workers, bool) or max_workers <= 0:
            raise ValidationError("scheduler max_workers must be positive")
        if (
            isinstance(aging_interval_ms, bool)
            or isinstance(aging_increment, bool)
            or aging_interval_ms <= 0
            or aging_increment <= 0
        ):
            raise ValidationError("scheduler aging settings must be positive")
        if (
            isinstance(starvation_threshold_ms, bool)
            or starvation_threshold_ms <= 0
        ):
            raise ValidationError(
                "scheduler starvation_threshold_ms must be positive"
            )
        self._policy = policy
        self._max_workers = max_workers
        self._aging_interval_ms = aging_interval_ms
        self._aging_increment = aging_increment
        self._starvation_threshold_ms = starvation_threshold_ms
        self._condition = Condition()
        self._records: dict[str, _RequestRecord] = {}
        self._workers: list[Thread] = []
        self._monitor: Thread | None = None
        self._sequence = 0
        self._started = False
        self._accepting = False
        self._stopping = False
        self._running_ids: set[str] = set()
        self._peak_queue_depth = 0
        self._submitted = 0
        self._started_count = 0
        self._completed = 0
        self._cancelled = 0
        self._timed_out = 0
        self._failed = 0
        self._starvation_promotions = 0
        self._queue_waits: list[float] = []
        self._execution_order: list[str] = []

    def start(self) -> None:
        with self._condition:
            if self._started:
                raise SchedulerLifecycleError("scheduler is already running")
            self._started = True
            self._accepting = True
            self._stopping = False
            self._workers = [
                Thread(
                    target=self._worker,
                    name=f"scheduler-worker-{index}",
                    daemon=True,
                )
                for index in range(self._max_workers)
            ]
            for worker in self._workers:
                worker.start()
            self._monitor = Thread(
                target=self._monitor_queue,
                name="scheduler-queue-monitor",
                daemon=True,
            )
            self._monitor.start()

    def submit(
        self,
        task: Task,
        operation: ScheduledOperation,
        options: SchedulingOptions | None = None,
    ) -> ScheduledRequestHandle:
        resolved = options or SchedulingOptions()
        with self._condition:
            if not self._started or not self._accepting:
                raise SchedulerLifecycleError("scheduler is not accepting requests")
            now = perf_counter()
            queued = self._queued_records_locked()
            record = _RequestRecord(
                request_id=str(uuid4()),
                task=task,
                sequence=self._sequence,
                operation=operation,
                options=resolved,
                token=resolved.cancellation or CancellationToken(),
                submitted_at=utc_now(),
                submitted_monotonic=now,
                queue_position_at_submit=len(queued) + 1,
                effective_priority=resolved.resolved_priority,
            )
            self._sequence += 1
            self._records[record.request_id] = record
            self._submitted += 1
            if record.token.is_cancelled:
                self._finish_locked(
                    record,
                    SchedulerRequestStatus.CANCELLED,
                    SchedulerCancelledError(
                        "scheduler request was cancelled before queueing",
                        details={"request_id": record.request_id},
                    ),
                )
            else:
                self._peak_queue_depth = max(
                    self._peak_queue_depth,
                    len(queued) + 1,
                )
            self._condition.notify_all()
            return ScheduledRequestHandle(self, record)

    def execute(
        self,
        task: Task,
        operation: ScheduledOperation,
        options: SchedulingOptions | None = None,
    ) -> ScheduledExecutionResult:
        return self.submit(task, operation, options).result()

    def cancel(self, request_id: str) -> bool:
        with self._condition:
            record = self._require_record_locked(request_id)
            if record.status in {
                SchedulerRequestStatus.COMPLETED,
                SchedulerRequestStatus.CANCELLED,
                SchedulerRequestStatus.TIMED_OUT,
                SchedulerRequestStatus.FAILED,
            }:
                return False
            record.token.cancel()
            if record.status is SchedulerRequestStatus.QUEUED:
                self._finish_locked(
                    record,
                    SchedulerRequestStatus.CANCELLED,
                    SchedulerCancelledError(
                        "queued scheduler request was cancelled",
                        details={"request_id": request_id},
                    ),
                )
            self._condition.notify_all()
            return True

    def request_snapshot(self, request_id: str) -> SchedulerRequestSnapshot:
        with self._condition:
            record = self._require_record_locked(request_id)
            return self._snapshot_record_locked(record, perf_counter())

    def snapshot(self) -> SchedulerMetrics:
        with self._condition:
            now = perf_counter()
            waits = sorted(self._queue_waits)
            return SchedulerMetrics(
                policy=self._policy,
                max_workers=self._max_workers,
                queue_depth=len(self._queued_records_locked()),
                running=len(self._running_ids),
                peak_queue_depth=self._peak_queue_depth,
                submitted=self._submitted,
                started=self._started_count,
                completed=self._completed,
                cancelled=self._cancelled,
                timed_out=self._timed_out,
                failed=self._failed,
                starvation_promotions=self._starvation_promotions,
                queue_wait_p50_ms=self._percentile(waits, 0.50),
                queue_wait_p95_ms=self._percentile(waits, 0.95),
                queue_wait_max_ms=max(waits) if waits else None,
                execution_order=tuple(self._execution_order),
                requests=tuple(
                    self._snapshot_record_locked(record, now)
                    for record in sorted(
                        self._records.values(), key=lambda item: item.sequence
                    )
                ),
            )

    def wait_until_idle(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else perf_counter() + timeout
        with self._condition:
            while self._queued_records_locked() or self._running_ids:
                remaining = None if deadline is None else deadline - perf_counter()
                if remaining is not None and remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return True

    def shutdown(self) -> None:
        with self._condition:
            if not self._started:
                return
            self._accepting = False
            self._stopping = True
            for record in self._records.values():
                if record.status is SchedulerRequestStatus.QUEUED:
                    record.token.cancel()
                    self._finish_locked(
                        record,
                        SchedulerRequestStatus.CANCELLED,
                        SchedulerCancelledError(
                            "scheduler shutdown cancelled queued request",
                            details={"request_id": record.request_id},
                        ),
                    )
                elif record.status is SchedulerRequestStatus.RUNNING:
                    record.token.cancel()
            self._condition.notify_all()
            workers = tuple(self._workers)
            monitor = self._monitor
        for worker in workers:
            worker.join(timeout=1.0)
        if monitor is not None:
            monitor.join(timeout=1.0)
        with self._condition:
            self._workers.clear()
            self._monitor = None
            self._started = False
            self._running_ids.clear()
            self._condition.notify_all()

    def _worker(self) -> None:
        while True:
            with self._condition:
                self._expire_queued_locked(perf_counter())
                record = self._select_next_locked(perf_counter())
                if record is None:
                    if self._stopping:
                        return
                    self._condition.wait(0.01)
                    continue
                now = perf_counter()
                record.status = SchedulerRequestStatus.RUNNING
                record.started_at = utc_now()
                record.started_monotonic = now
                record.queue_wait_ms = (now - record.submitted_monotonic) * 1_000
                self._queue_waits.append(record.queue_wait_ms)
                self._running_ids.add(record.request_id)
                self._started_count += 1
                self._execution_order.append(record.task.task_id)
            value, error = self._run_bounded(record)
            with self._condition:
                self._running_ids.discard(record.request_id)
                if error is None and value is not None:
                    record.value = value
                    self._finish_locked(
                        record,
                        SchedulerRequestStatus.COMPLETED,
                        None,
                    )
                elif isinstance(error, TaskTimeoutError):
                    self._finish_locked(
                        record,
                        SchedulerRequestStatus.TIMED_OUT,
                        error,
                    )
                elif isinstance(
                    error, (SchedulerCancelledError, InferenceCancelledError)
                ):
                    self._finish_locked(
                        record,
                        SchedulerRequestStatus.CANCELLED,
                        error,
                    )
                else:
                    self._finish_locked(
                        record,
                        SchedulerRequestStatus.FAILED,
                        error or SchedulerLifecycleError("scheduled operation returned no result"),
                    )
                self._condition.notify_all()

    def _monitor_queue(self) -> None:
        while True:
            with self._condition:
                if self._stopping:
                    return
                self._expire_queued_locked(perf_counter())
                self._condition.notify_all()
                self._condition.wait(0.01)

    def _run_bounded(
        self,
        record: _RequestRecord,
    ) -> tuple[InferenceResult | None, BaseException | None]:
        outcomes: Queue[tuple[str, object]] = Queue(maxsize=1)

        def invoke() -> None:
            try:
                outcomes.put(("result", record.operation(record.token)))
            except Exception as error:
                outcomes.put(("error", error))

        Thread(
            target=invoke,
            name=f"scheduled-operation-{record.request_id[:8]}",
            daemon=True,
        ).start()
        deadline = (
            record.submitted_monotonic + record.options.timeout_ms / 1_000
            if record.options.timeout_ms is not None
            else None
        )
        while True:
            now = perf_counter()
            if deadline is not None and now >= deadline:
                record.token.cancel()
                return None, TaskTimeoutError(
                    "scheduler request exceeded its end-to-end timeout",
                    details={
                        "request_id": record.request_id,
                        "task_id": record.task.task_id,
                        "timeout_ms": record.options.timeout_ms,
                        "scope": "queue_and_execution",
                    },
                )
            if record.token.is_cancelled:
                return None, SchedulerCancelledError(
                    "running scheduler request was cancelled",
                    details={
                        "request_id": record.request_id,
                        "task_id": record.task.task_id,
                    },
                )
            wait = 0.01
            if deadline is not None:
                wait = min(wait, max(0.0, deadline - now))
            try:
                outcome, payload = outcomes.get(timeout=wait)
            except Empty:
                continue
            now = perf_counter()
            if deadline is not None and now >= deadline:
                record.token.cancel()
                return None, TaskTimeoutError(
                    "scheduler request exceeded its end-to-end timeout",
                    details={
                        "request_id": record.request_id,
                        "task_id": record.task.task_id,
                        "timeout_ms": record.options.timeout_ms,
                        "scope": "queue_and_execution",
                    },
                )
            if record.token.is_cancelled:
                return None, SchedulerCancelledError(
                    "running scheduler request was cancelled",
                    details={
                        "request_id": record.request_id,
                        "task_id": record.task.task_id,
                    },
                )
            if outcome == "error":
                return None, payload if isinstance(payload, BaseException) else None
            if not isinstance(payload, InferenceResult):
                return None, SchedulerLifecycleError(
                    "scheduled operation returned the wrong result type",
                    details={
                        "request_id": record.request_id,
                        "actual_type": type(payload).__name__,
                    },
                )
            return payload, None

    def _select_next_locked(self, now: float) -> _RequestRecord | None:
        queued = self._queued_records_locked()
        if not queued:
            return None
        starved = [
            record
            for record in queued
            if (now - record.submitted_monotonic) * 1_000
            >= self._starvation_threshold_ms
        ]
        if starved:
            selected = min(starved, key=lambda item: item.sequence)
            self._starvation_promotions += 1
            selected.effective_priority = self._effective_priority(selected, now)
            return selected
        if self._policy is SchedulerPolicy.FIFO:
            selected = min(queued, key=lambda item: item.sequence)
            selected.effective_priority = selected.options.resolved_priority
            return selected
        for record in queued:
            record.effective_priority = self._effective_priority(record, now)
        return min(
            queued,
            key=lambda item: (-item.effective_priority, item.sequence),
        )

    def _effective_priority(self, record: _RequestRecord, now: float) -> int:
        waited_ms = max(0.0, (now - record.submitted_monotonic) * 1_000)
        aging_steps = int(waited_ms // self._aging_interval_ms)
        return record.options.resolved_priority + aging_steps * self._aging_increment

    def _expire_queued_locked(self, now: float) -> None:
        for record in self._queued_records_locked():
            if record.token.is_cancelled:
                self._finish_locked(
                    record,
                    SchedulerRequestStatus.CANCELLED,
                    SchedulerCancelledError(
                        "queued scheduler request was cancelled",
                        details={"request_id": record.request_id},
                    ),
                )
                continue
            timeout_ms = record.options.timeout_ms
            if (
                timeout_ms is not None
                and (now - record.submitted_monotonic) * 1_000 >= timeout_ms
            ):
                record.token.cancel()
                self._finish_locked(
                    record,
                    SchedulerRequestStatus.TIMED_OUT,
                    TaskTimeoutError(
                        "scheduler request timed out while queued",
                        details={
                            "request_id": record.request_id,
                            "task_id": record.task.task_id,
                            "timeout_ms": timeout_ms,
                            "scope": "queue",
                        },
                    ),
                )

    def _finish_locked(
        self,
        record: _RequestRecord,
        status: SchedulerRequestStatus,
        error: BaseException | None,
    ) -> None:
        if record.completion.is_set():
            return
        record.status = status
        record.error = error
        record.finished_at = utc_now()
        if record.started_monotonic is not None:
            record.execution_ms = (perf_counter() - record.started_monotonic) * 1_000
        if status is SchedulerRequestStatus.COMPLETED:
            self._completed += 1
        elif status is SchedulerRequestStatus.CANCELLED:
            self._cancelled += 1
        elif status is SchedulerRequestStatus.TIMED_OUT:
            self._timed_out += 1
        elif status is SchedulerRequestStatus.FAILED:
            self._failed += 1
        record.completion.set()

    def _snapshot_record_locked(
        self,
        record: _RequestRecord,
        now: float,
    ) -> SchedulerRequestSnapshot:
        effective = (
            self._effective_priority(record, now)
            if record.status is SchedulerRequestStatus.QUEUED
            else record.effective_priority
        )
        error_code = (
            record.error.code if isinstance(record.error, LabError) else None
        )
        return SchedulerRequestSnapshot(
            request_id=record.request_id,
            task_id=record.task.task_id,
            sequence=record.sequence,
            status=record.status,
            workload=record.options.workload,
            base_priority=record.options.resolved_priority,
            effective_priority=effective,
            queue_position_at_submit=record.queue_position_at_submit,
            submitted_at=record.submitted_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
            queue_wait_ms=record.queue_wait_ms,
            execution_ms=record.execution_ms,
            timeout_ms=record.options.timeout_ms,
            error_code=error_code,
        )

    def _queued_records_locked(self) -> list[_RequestRecord]:
        return [
            record
            for record in self._records.values()
            if record.status is SchedulerRequestStatus.QUEUED
        ]

    def _require_record_locked(self, request_id: str) -> _RequestRecord:
        try:
            return self._records[request_id]
        except KeyError as error:
            raise SchedulerLifecycleError(
                "scheduler request does not exist",
                details={"request_id": request_id},
            ) from error

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float | None:
        if not values:
            return None
        index = max(0, min(len(values) - 1, ceil(len(values) * percentile) - 1))
        return values[index]
