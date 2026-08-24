"""Narrow protocol adapters over the shared SQLite runtime store."""

from __future__ import annotations

from collections.abc import Sequence

from ..models import Agent, Checkpoint, LifecycleEvent, MetricEvent, StateTransition, TaskState
from .sqlite_store import SQLiteRuntimeStore


class SQLiteAgentRegistry:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self.store = store

    def register(self, agent: Agent) -> None:
        self.store.register(agent)

    def get(self, agent_id: str) -> Agent:
        return self.store.get(agent_id)

    def snapshot(self) -> Sequence[Agent]:
        return self.store.snapshot()  # type: ignore[return-value]


class SQLiteLifecycleEventStore:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self.store = store

    def append(self, event: LifecycleEvent) -> None:
        self.store.append(event)

    def snapshot(self, task_id: str | None = None) -> Sequence[LifecycleEvent]:
        return self.store.lifecycle_snapshot(task_id)


class SQLiteMetricsCollector:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self.store = store

    def record(self, event: MetricEvent) -> None:
        self.store.record(event)

    def snapshot(self) -> Sequence[MetricEvent]:
        return self.store.metric_snapshot()


class SQLiteCheckpointStore:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self.store = store

    def save(self, checkpoint: Checkpoint) -> None:
        self.store.save(checkpoint)

    def latest(self, task_id: str) -> Checkpoint | None:
        return self.store.latest(task_id)

    def for_task(self, task_id: str) -> tuple[Checkpoint, ...]:
        return self.store.for_task(task_id)


class SQLiteTaskStateMachine:
    def __init__(self, store: SQLiteRuntimeStore) -> None:
        self.store = store

    def initialize(self, task_id: str, *, reason: str) -> StateTransition:
        return self.store.initialize(task_id, reason=reason)

    def transition(self, task_id: str, to_state: TaskState, *, reason: str) -> StateTransition:
        return self.store.transition(task_id, to_state, reason=reason)

    def current(self, task_id: str) -> TaskState:
        return self.store.current(task_id)

    def history(self, task_id: str) -> Sequence[StateTransition]:
        return self.store.history(task_id)
