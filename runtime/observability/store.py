"""Narrow Stage 12 observability source over SQLite persistence."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..persistence.sqlite_store import SQLiteRuntimeStore


class SQLiteObservabilitySource:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self._store = store

    def query(
        self,
        *,
        since: datetime,
        recent_task_limit: int,
        recent_event_limit: int,
    ) -> dict[str, Any]:
        return self._store.observability_data(
            since=since,
            recent_task_limit=recent_task_limit,
            recent_event_limit=recent_event_limit,
        )
