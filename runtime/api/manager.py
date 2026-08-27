"""Bounded asynchronous ownership of AgentRuntime tasks for the HTTP API."""

from __future__ import annotations

from threading import BoundedSemaphore, RLock, Thread
from typing import Any

from ..cancellation import CancellationToken
from ..engine import AgentRuntime
from ..errors import (
    ApiCapacityError,
    ApiConflictError,
    LabError,
    TaskNotFoundError,
)
from ..models import LifecycleEvent, TaskState, utc_now
from ..scheduler import SchedulingOptions, WorkloadClass
from .models import ApiTaskRecord, ApiTaskStatus


class ApiTaskManager:
    def __init__(self, runtime: AgentRuntime, *, max_inflight_tasks: int) -> None:
        self.runtime = runtime
        self._records: dict[str, ApiTaskRecord] = {}
        self._threads: dict[str, Thread] = {}
        self._lock = RLock()
        self._capacity = BoundedSemaphore(max_inflight_tasks)

    def create(
        self,
        *,
        agent_id: str,
        objective: str | None,
        input_data: dict[str, Any] | None,
        workload: WorkloadClass,
        timeout_ms: int,
    ) -> ApiTaskRecord:
        if not self._capacity.acquire(blocking=False):
            raise ApiCapacityError("API in-flight task capacity is exhausted")
        try:
            agent = self.runtime.components.agents.get(agent_id)
            task = self.runtime.create_task(
                agent=agent,
                objective=objective if objective is not None else agent.objective,
                input_data=input_data,
            )
            record = ApiTaskRecord(task=task, cancellation=CancellationToken())
            worker = Thread(
                target=self._execute,
                args=(record, agent, workload, timeout_ms),
                name=f"api-task-{task.task_id[:8]}",
                daemon=True,
            )
            with self._lock:
                self._records[task.task_id] = record
                self._threads[task.task_id] = worker
            worker.start()
            return record
        except Exception:
            self._capacity.release()
            raise

    def _execute(
        self,
        record: ApiTaskRecord,
        agent: Any,
        workload: WorkloadClass,
        timeout_ms: int,
    ) -> None:
        with self._lock:
            record.status = ApiTaskStatus.RUNNING
            record.started_at = utc_now()
        try:
            result = self.runtime.execute_task(
                task=record.task,
                agent=agent,
                scheduling=SchedulingOptions(
                    workload=workload,
                    timeout_ms=timeout_ms,
                    cancellation=record.cancellation,
                ),
            )
            with self._lock:
                record.result = result
                record.status = ApiTaskStatus.COMPLETED
        except LabError as error:
            with self._lock:
                record.error = error.as_dict()
                state = self.runtime.task_state(record.task.task_id)
                record.status = {
                    TaskState.CANCELLED: ApiTaskStatus.CANCELLED,
                    TaskState.TIMEOUT: ApiTaskStatus.TIMED_OUT,
                }.get(state, ApiTaskStatus.FAILED)
        except Exception as error:
            with self._lock:
                record.error = {
                    "code": "api_task_failed",
                    "message": "task failed in an unexpected runtime boundary",
                    "details": {"cause_type": type(error).__name__},
                }
                record.status = ApiTaskStatus.FAILED
        finally:
            with self._lock:
                record.finished_at = utc_now()
            self._capacity.release()

    def get(self, task_id: str) -> ApiTaskRecord:
        with self._lock:
            record = self._records.get(task_id)
        if record is None:
            raise TaskNotFoundError("API task is not known", details={"task_id": task_id})
        return record

    def inspect(self, task_id: str) -> dict[str, Any]:
        try:
            record = self.get(task_id)
        except TaskNotFoundError:
            persistence = self.runtime.components.persistence
            if persistence is None:
                raise
            task = persistence.load_task(task_id)
            state = self.runtime.task_state(task_id)
            status = {
                TaskState.COMPLETED: ApiTaskStatus.COMPLETED.value,
                TaskState.CANCELLED: ApiTaskStatus.CANCELLED.value,
                TaskState.TIMEOUT: ApiTaskStatus.TIMED_OUT.value,
            }.get(state, ApiTaskStatus.FAILED.value if state in {
                TaskState.MODEL_FAILED,
                TaskState.TOOL_FAILED,
                TaskState.INVALID_OUTPUT,
                TaskState.OUT_OF_MEMORY,
                TaskState.SECURITY_BLOCKED,
                TaskState.CONTEXT_OVERFLOW,
                TaskState.RESOURCE_BLOCKED,
            } else "durable")
            durable_output = persistence.load_task_output(task_id)
            result: dict[str, Any] | None = durable_output
            if durable_output is not None and durable_output["output_type"] == "inference":
                stored = durable_output["output"]
                result = {
                    "output_type": "inference",
                    "task_id": stored.get("task_id", task.task_id),
                    "agent_id": stored.get("agent_id", task.agent_id),
                    "objective": stored.get("objective", task.objective),
                    "output": stored.get("output"),
                    "model_id": stored.get("model_id"),
                    "backend_name": stored.get("backend_name"),
                    "final_state": stored.get("final_state", state.value),
                    "metadata": dict(stored.get("metadata", {})),
                    "inference_metrics": stored.get("metrics"),
                    "state_history": [
                        {
                            "sequence": item.sequence,
                            "from_state": item.from_state.value if item.from_state else None,
                            "to_state": item.to_state.value,
                            "reason": item.reason,
                            "recorded_at_utc": item.recorded_at.isoformat(),
                        }
                        for item in self.runtime.state_history(task_id)
                    ],
                }
            return {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "objective": task.objective,
                "input_data": dict(task.input_data),
                "status": status,
                "durable_state": state.value,
                "cancellation_requested": False,
                "accepted_at_utc": task.created_at.isoformat(),
                "started_at_utc": None,
                "finished_at_utc": None,
                "result": result,
                "error": None,
                "links": {
                    "self": f"/v1/tasks/{task_id}",
                    "events": f"/v1/tasks/{task_id}/events",
                    "trace": f"/v1/tasks/{task_id}/trace",
                },
            }
        try:
            durable_state = self.runtime.task_state(task_id).value
        except LabError:
            durable_state = None
        with self._lock:
            return record.as_dict(durable_state=durable_state)

    def cancel(self, task_id: str) -> dict[str, Any]:
        record = self.get(task_id)
        with self._lock:
            if record.terminal:
                raise ApiConflictError(
                    "terminal task cannot be cancelled",
                    details={"task_id": task_id, "status": record.status.value},
                )
            record.cancellation_requested = True
            record.cancellation.cancel()
        return self.inspect(task_id)

    def events(self, task_id: str) -> tuple[LifecycleEvent, ...]:
        self.get(task_id)
        return tuple(self.runtime.components.events.snapshot(task_id))

    def wait(self, task_id: str, timeout: float | None = None) -> bool:
        self.get(task_id)
        with self._lock:
            thread = self._threads.get(task_id)
        if thread is None:
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def shutdown(self) -> None:
        with self._lock:
            records = tuple(self._records.values())
            threads = tuple(self._threads.values())
            for record in records:
                if not record.terminal:
                    record.cancellation_requested = True
                    record.cancellation.cancel()
        for thread in threads:
            thread.join(timeout=5.0)
