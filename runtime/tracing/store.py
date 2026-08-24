"""Narrow trace-store adapter over Stage 10 SQLite persistence."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .models import ReplayReport, TraceRun, TraceStep

if TYPE_CHECKING:
    from ..persistence.sqlite_store import SQLiteRuntimeStore


class SQLiteTraceStore:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self._store = store

    def for_task(self, task_id: str) -> TraceRun:
        return self._store.trace_run_for_task(task_id)

    def load_run(self, run_id: str) -> TraceRun:
        return self._store.load_trace_run(run_id)

    def steps(self, run_id: str) -> Sequence[TraceStep]:
        return self._store.trace_steps(run_id)

    def list_runs(self) -> Sequence[TraceRun]:
        return self._store.list_trace_runs()

    def save_replay(self, report: ReplayReport) -> None:
        self._store.save_trace_replay(report)
