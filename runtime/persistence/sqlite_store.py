"""SQLite-backed Stage 10 runtime stores and recovery ledger."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from ..errors import (
    AgentNotFoundError,
    DuplicateAgentError,
    IllegalStateTransitionError,
    TaskNotFoundError,
)
from ..models import (
    Agent,
    Checkpoint,
    LifecycleEvent,
    MetricEvent,
    StateTransition,
    Task,
    TaskResult,
    TaskState,
    ToolCapabilityMetadata,
    utc_now,
)
from ..state_machine import LEGAL_TRANSITIONS, TERMINAL_STATES
from ..tools.models import ToolRequest, ToolResult
from ..tracing.hashing import (
    GENESIS_HASH,
    actor_component,
    classify_event,
    compute_step_hash,
    hash_payload,
    semantic_hash,
    stable_step_id,
)
from ..tracing.models import (
    DeterminismClass,
    ReplayReport,
    TraceRun,
    TraceStep,
)
from .config import PersistenceConfig
from .models import RecoveryCandidate, RecoveryDisposition


SCHEMA_VERSION = 2


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _mapping(value: str | None) -> dict[str, Any]:
    return dict(json.loads(value or "{}"))


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SQLiteRuntimeStore:
    """One database implementing durable registries, stores, and state history."""

    def __init__(self, config: PersistenceConfig) -> None:
        self.config = config
        self.path = config.database_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            self.path,
            timeout=self.config.busy_timeout_ms / 1000.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self.config.busy_timeout_ms}")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    def _initialize_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            connection.execute(f"PRAGMA synchronous = {self.config.synchronous}")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at_utc TEXT NOT NULL)"
            )
            connection.commit()
            row = connection.execute(
                "SELECT MAX(version) AS version FROM schema_migrations"
            ).fetchone()
            current = row["version"] if row is not None else None
            if current is not None and int(current) > SCHEMA_VERSION:
                raise sqlite3.DatabaseError("database schema is newer than this runtime")
            try:
                connection.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at_utc TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS agents (
                        agent_id TEXT PRIMARY KEY,
                        payload_json TEXT NOT NULL,
                        updated_at_utc TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        objective TEXT NOT NULL,
                        input_json TEXT NOT NULL,
                        created_at_utc TEXT NOT NULL,
                        current_state TEXT,
                        updated_at_utc TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS state_transitions (
                        task_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        from_state TEXT,
                        to_state TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL,
                        PRIMARY KEY (task_id, sequence),
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        phase TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL,
                        data_json TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS lifecycle_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL,
                        agent_id TEXT,
                        task_id TEXT,
                        state TEXT,
                        data_json TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS metric_events (
                        metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL,
                        task_id TEXT,
                        attributes_json TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS execution_steps (
                        step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        state TEXT,
                        recorded_at_utc TEXT NOT NULL,
                        data_json TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS model_configurations (
                        configuration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        runtime_name TEXT NOT NULL,
                        model_id TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS tool_calls (
                        request_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        agent_id TEXT NOT NULL,
                        tool_name TEXT NOT NULL,
                        arguments_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        result_json TEXT,
                        error_json TEXT,
                        started_at_utc TEXT NOT NULL,
                        finished_at_utc TEXT,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS outputs (
                        task_id TEXT PRIMARY KEY,
                        output_type TEXT NOT NULL,
                        output_json TEXT NOT NULL,
                        recorded_at_utc TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS recovery_attempts (
                        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        checkpoint_phase TEXT NOT NULL,
                        status TEXT NOT NULL,
                        started_at_utc TEXT NOT NULL,
                        finished_at_utc TEXT,
                        details_json TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                    );
                    CREATE TABLE IF NOT EXISTS trace_runs (
                        run_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL UNIQUE,
                        source_run_id TEXT,
                        started_at_utc TEXT NOT NULL,
                        finished_at_utc TEXT,
                        status TEXT NOT NULL,
                        model_id TEXT,
                        configuration_hash TEXT,
                        final_chain_hash TEXT,
                        metadata_json TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id),
                        FOREIGN KEY (source_run_id) REFERENCES trace_runs(run_id)
                    );
                    CREATE TABLE IF NOT EXISTS trace_steps (
                        run_id TEXT NOT NULL,
                        ordinal INTEGER NOT NULL,
                        step_id TEXT NOT NULL UNIQUE,
                        recorded_at_utc TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        component TEXT NOT NULL,
                        event_name TEXT NOT NULL,
                        determinism TEXT NOT NULL,
                        input_json TEXT NOT NULL,
                        input_hash TEXT NOT NULL,
                        output_json TEXT NOT NULL,
                        output_hash TEXT NOT NULL,
                        semantic_hash TEXT NOT NULL,
                        state_from TEXT,
                        state_to TEXT,
                        model_id TEXT,
                        configuration_hash TEXT,
                        failure_json TEXT,
                        previous_hash TEXT NOT NULL,
                        step_hash TEXT NOT NULL,
                        PRIMARY KEY (run_id, ordinal),
                        FOREIGN KEY (run_id) REFERENCES trace_runs(run_id)
                    );
                    CREATE TABLE IF NOT EXISTS trace_replays (
                        replay_id TEXT PRIMARY KEY,
                        source_run_id TEXT NOT NULL,
                        started_at_utc TEXT NOT NULL,
                        finished_at_utc TEXT NOT NULL,
                        status TEXT NOT NULL,
                        report_json TEXT NOT NULL,
                        FOREIGN KEY (source_run_id) REFERENCES trace_runs(run_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_task ON checkpoints(task_id, checkpoint_id);
                    CREATE INDEX IF NOT EXISTS idx_events_task ON lifecycle_events(task_id, event_id);
                    CREATE INDEX IF NOT EXISTS idx_steps_task ON execution_steps(task_id, step_id);
                    CREATE INDEX IF NOT EXISTS idx_trace_runs_task ON trace_runs(task_id);
                    CREATE INDEX IF NOT EXISTS idx_trace_steps_event ON trace_steps(run_id, event_name, ordinal);
                    INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc)
                    VALUES (1, strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now'));
                    INSERT OR IGNORE INTO schema_migrations(version, applied_at_utc)
                    VALUES (2, strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now'));
                    COMMIT;
                    """
                )
            except Exception:
                connection.rollback()
                raise

    @property
    def schema_version(self) -> int:
        with self._connection() as connection:
            row = connection.execute("SELECT MAX(version) AS version FROM schema_migrations").fetchone()
            return int(row["version"])

    @staticmethod
    def _agent_payload(agent: Agent) -> dict[str, Any]:
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "objective": agent.objective,
            "capabilities": sorted(agent.capabilities),
            "system_prompt": agent.system_prompt,
            "tool_capabilities": [
                {
                    "name": item.name,
                    "description": item.description,
                    "permissions": sorted(item.permissions),
                }
                for item in agent.tool_capabilities
            ],
        }

    @staticmethod
    def _agent_from_payload(payload: dict[str, Any]) -> Agent:
        return Agent(
            agent_id=str(payload["agent_id"]),
            name=str(payload["name"]),
            objective=str(payload["objective"]),
            capabilities=frozenset(str(item) for item in payload["capabilities"]),
            system_prompt=str(payload["system_prompt"]),
            tool_capabilities=tuple(
                ToolCapabilityMetadata(
                    name=str(item["name"]),
                    description=str(item["description"]),
                    permissions=frozenset(str(value) for value in item["permissions"]),
                )
                for item in payload["tool_capabilities"]
            ),
        )

    def register(self, agent: Agent) -> None:
        with self._transaction() as connection:
            if connection.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent.agent_id,)).fetchone():
                raise DuplicateAgentError(
                    "agent identity is already registered",
                    details={"agent_id": agent.agent_id},
                )
            connection.execute(
                "INSERT INTO agents(agent_id, payload_json, updated_at_utc) VALUES (?, ?, ?)",
                (agent.agent_id, _json(self._agent_payload(agent)), utc_now().isoformat()),
            )

    def ensure_agent(self, agent: Agent) -> None:
        payload = _json(self._agent_payload(agent))
        with self._transaction() as connection:
            row = connection.execute("SELECT payload_json FROM agents WHERE agent_id = ?", (agent.agent_id,)).fetchone()
            if row is not None and row["payload_json"] != payload:
                raise DuplicateAgentError(
                    "durable agent identity conflicts with the configured definition",
                    details={"agent_id": agent.agent_id},
                )
            connection.execute(
                "INSERT INTO agents(agent_id, payload_json, updated_at_utc) VALUES (?, ?, ?) "
                "ON CONFLICT(agent_id) DO UPDATE SET updated_at_utc=excluded.updated_at_utc",
                (agent.agent_id, payload, utc_now().isoformat()),
            )

    def save_agent(self, agent: Agent) -> None:
        self.ensure_agent(agent)

    def get(self, agent_id: str) -> Agent:
        with self._connection() as connection:
            row = connection.execute("SELECT payload_json FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
        if row is None:
            raise AgentNotFoundError("agent identity is not registered", details={"agent_id": agent_id})
        return self._agent_from_payload(_mapping(row["payload_json"]))

    def snapshot(self, task_id: str | None = None) -> Sequence[Any]:
        if task_id is None:
            with self._connection() as connection:
                rows = connection.execute("SELECT payload_json FROM agents ORDER BY agent_id").fetchall()
            return tuple(self._agent_from_payload(_mapping(row["payload_json"])) for row in rows)
        return self.lifecycle_snapshot(task_id)

    def save_task(self, task: Task) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO tasks(task_id, agent_id, objective, input_json, created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
                (task.task_id, task.agent_id, task.objective, _json(task.input_data), task.created_at.isoformat(), utc_now().isoformat()),
            )
            config_row = connection.execute(
                "SELECT model_id, payload_json FROM model_configurations ORDER BY configuration_id DESC LIMIT 1"
            ).fetchone()
            configuration_hash = (
                hash_payload(json.loads(config_row["payload_json"]))
                if config_row is not None
                else None
            )
            run_id = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO trace_runs(run_id, task_id, started_at_utc, status, model_id, configuration_hash, metadata_json) VALUES (?, ?, ?, 'running', ?, ?, ?)",
                (
                    run_id,
                    task.task_id,
                    task.created_at.isoformat(),
                    config_row["model_id"] if config_row is not None else None,
                    configuration_hash,
                    _json(
                        {
                            "agent_id": task.agent_id,
                            "objective_hash": hash_payload(task.objective),
                            "input_hash": hash_payload(task.input_data),
                        }
                    ),
                ),
            )

    def load_task(self, task_id: str) -> Task:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise TaskNotFoundError("durable task does not exist", details={"task_id": task_id})
        return Task(row["task_id"], row["agent_id"], row["objective"], _datetime(row["created_at_utc"]), _mapping(row["input_json"]))

    def load_task_output(self, task_id: str) -> dict[str, Any] | None:
        """Load the latest durable output without re-executing the task."""

        with self._connection() as connection:
            row = connection.execute(
                "SELECT output_type, output_json, recorded_at_utc FROM outputs WHERE task_id=?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "output_type": str(row["output_type"]),
            "output": _mapping(row["output_json"]),
            "recorded_at_utc": str(row["recorded_at_utc"]),
        }

    def initialize(self, task_id: str, *, reason: str) -> StateTransition:
        transition = StateTransition(0, None, TaskState.CREATED, reason)
        with self._transaction() as connection:
            row = connection.execute("SELECT current_state FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None:
                raise TaskNotFoundError("durable task does not exist", details={"task_id": task_id})
            if row["current_state"] is not None:
                raise IllegalStateTransitionError("task state machine is already initialized", details={"task_id": task_id})
            connection.execute(
                "INSERT INTO state_transitions VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, 0, None, TaskState.CREATED.value, reason, transition.recorded_at.isoformat()),
            )
            connection.execute("UPDATE tasks SET current_state=?, updated_at_utc=? WHERE task_id=?", (TaskState.CREATED.value, transition.recorded_at.isoformat(), task_id))
        return transition

    def transition(self, task_id: str, to_state: TaskState, *, reason: str) -> StateTransition:
        with self._transaction() as connection:
            row = connection.execute("SELECT current_state FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None or row["current_state"] is None:
                raise TaskNotFoundError("task state machine is not initialized", details={"task_id": task_id})
            current = TaskState(row["current_state"])
            if to_state not in LEGAL_TRANSITIONS[current]:
                raise IllegalStateTransitionError(
                    "task state transition is not legal",
                    details={
                        "task_id": task_id,
                        "current_state": current.value,
                        "requested_state": to_state.value,
                        "allowed_states": sorted(item.value for item in LEGAL_TRANSITIONS[current]),
                    },
                )
            sequence = int(connection.execute("SELECT COUNT(*) AS count FROM state_transitions WHERE task_id=?", (task_id,)).fetchone()["count"])
            transition = StateTransition(sequence, current, to_state, reason)
            connection.execute(
                "INSERT INTO state_transitions VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, sequence, current.value, to_state.value, reason, transition.recorded_at.isoformat()),
            )
            connection.execute("UPDATE tasks SET current_state=?, updated_at_utc=? WHERE task_id=?", (to_state.value, transition.recorded_at.isoformat(), task_id))
            return transition

    def current(self, task_id: str) -> TaskState:
        with self._connection() as connection:
            row = connection.execute("SELECT current_state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None or row["current_state"] is None:
            raise TaskNotFoundError("task state machine is not initialized", details={"task_id": task_id})
        return TaskState(row["current_state"])

    def history(self, task_id: str) -> tuple[StateTransition, ...]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM state_transitions WHERE task_id=? ORDER BY sequence", (task_id,)).fetchall()
        if not rows:
            raise TaskNotFoundError("task state machine is not initialized", details={"task_id": task_id})
        return tuple(
            StateTransition(
                int(row["sequence"]),
                TaskState(row["from_state"]) if row["from_state"] else None,
                TaskState(row["to_state"]),
                row["reason"],
                _datetime(row["recorded_at_utc"]),
            )
            for row in rows
        )

    def save(self, checkpoint: Checkpoint) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO checkpoints(task_id, phase, recorded_at_utc, data_json) VALUES (?, ?, ?, ?)",
                (checkpoint.task_id, checkpoint.phase, checkpoint.recorded_at.isoformat(), _json(checkpoint.data)),
            )

    def latest(self, task_id: str) -> Checkpoint | None:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM checkpoints WHERE task_id=? ORDER BY checkpoint_id DESC LIMIT 1", (task_id,)).fetchone()
        return self._checkpoint(row) if row is not None else None

    def for_task(self, task_id: str) -> tuple[Checkpoint, ...]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM checkpoints WHERE task_id=? ORDER BY checkpoint_id", (task_id,)).fetchall()
        return tuple(self._checkpoint(row) for row in rows)

    @staticmethod
    def _checkpoint(row: sqlite3.Row) -> Checkpoint:
        return Checkpoint(row["task_id"], row["phase"], _datetime(row["recorded_at_utc"]), _mapping(row["data_json"]))

    def append(self, event: LifecycleEvent) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO lifecycle_events(name, recorded_at_utc, agent_id, task_id, state, data_json) VALUES (?, ?, ?, ?, ?, ?)",
                (event.name, event.recorded_at.isoformat(), event.agent_id, event.task_id, event.state.value if event.state else None, _json(event.data)),
            )
            if event.task_id is not None:
                connection.execute(
                    "INSERT INTO execution_steps(task_id, kind, state, recorded_at_utc, data_json) VALUES (?, ?, ?, ?, ?)",
                    (event.task_id, event.name, event.state.value if event.state else None, event.recorded_at.isoformat(), _json(event.data)),
                )
                self._append_trace_step(
                    connection,
                    task_id=event.task_id,
                    event_name=event.name,
                    recorded_at=event.recorded_at,
                    input_data={
                        "agent_id": event.agent_id,
                        "task_id": event.task_id,
                        "state": event.state.value if event.state else None,
                    },
                    output_data=event.data,
                )

    def lifecycle_snapshot(self, task_id: str | None = None) -> tuple[LifecycleEvent, ...]:
        query = "SELECT * FROM lifecycle_events"
        parameters: tuple[Any, ...] = tuple()
        if task_id is not None:
            query += " WHERE task_id=?"
            parameters = (task_id,)
        query += " ORDER BY event_id"
        with self._connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(
            LifecycleEvent(row["name"], _datetime(row["recorded_at_utc"]), row["agent_id"], row["task_id"], TaskState(row["state"]) if row["state"] else None, _mapping(row["data_json"]))
            for row in rows
        )

    def record(self, event: MetricEvent) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO metric_events(name, recorded_at_utc, task_id, attributes_json) VALUES (?, ?, ?, ?)",
                (event.name, event.recorded_at.isoformat(), event.task_id, _json(event.attributes)),
            )

    def metric_snapshot(self) -> tuple[MetricEvent, ...]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM metric_events ORDER BY metric_id").fetchall()
        return tuple(MetricEvent(row["name"], _datetime(row["recorded_at_utc"]), row["task_id"], _mapping(row["attributes_json"])) for row in rows)

    def save_model_configuration(self, runtime_name: str, model_id: str, payload: dict[str, Any]) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO model_configurations(runtime_name, model_id, payload_json, recorded_at_utc) VALUES (?, ?, ?, ?)",
                (runtime_name, model_id, _json(payload), utc_now().isoformat()),
            )

    def save_task_result(self, result: TaskResult) -> None:
        payload = {
            "task_id": result.task_id,
            "output": result.output,
            "model_id": result.model_id,
            "backend_name": result.backend_name,
            "metadata": result.metadata,
            "metrics": result.inference_metrics.as_dict() if result.inference_metrics else None,
            "agent_id": result.agent_id,
            "objective": result.objective,
            "final_state": result.final_state.value if result.final_state else None,
        }
        self._save_output(
            result.task_id,
            "inference",
            payload,
            trace_event_name="inference.output.persisted",
            trace_input={
                "agent_id": result.agent_id,
                "objective_hash": hash_payload(result.objective),
                "model_id": result.model_id,
            },
        )

    def save_tool_request(self, request: ToolRequest) -> None:
        with self._transaction() as connection:
            recorded_at = utc_now()
            connection.execute(
                "INSERT INTO tool_calls(request_id, task_id, agent_id, tool_name, arguments_json, status, started_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (request.request_id, request.task_id, request.agent_id, request.tool_name, _json(request.arguments), "running", recorded_at.isoformat()),
            )
            self._append_trace_step(
                connection,
                task_id=request.task_id,
                event_name="tool.request.persisted",
                recorded_at=recorded_at,
                input_data={
                    "agent_id": request.agent_id,
                    "request_id": request.request_id,
                    "tool_name": request.tool_name,
                    "arguments": request.arguments,
                },
                output_data={"status": "running"},
            )

    def save_tool_result(self, result: ToolResult) -> None:
        with self._transaction() as connection:
            recorded_at = utc_now()
            connection.execute(
                "UPDATE tool_calls SET status=?, result_json=?, finished_at_utc=? WHERE request_id=?",
                ("completed" if result.success else "failed", _json(result.as_dict()), recorded_at.isoformat(), result.request_id),
            )
            self._append_trace_step(
                connection,
                task_id=result.task_id,
                event_name="tool.result.persisted",
                recorded_at=recorded_at,
                input_data={"request_id": result.request_id, "tool_name": result.tool_name},
                output_data=result.as_dict(),
            )
        self._save_output(
            result.task_id,
            "tool",
            result.as_dict(),
            trace_event_name="tool.output.persisted",
            trace_input={"request_id": result.request_id, "tool_name": result.tool_name},
        )

    def save_tool_error(self, request_id: str, error: dict[str, Any]) -> None:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT task_id, tool_name FROM tool_calls WHERE request_id=?",
                (request_id,),
            ).fetchone()
            recorded_at = utc_now()
            connection.execute(
                "UPDATE tool_calls SET status='failed', error_json=?, finished_at_utc=? WHERE request_id=?",
                (_json(error), recorded_at.isoformat(), request_id),
            )
            if row is not None:
                self._append_trace_step(
                    connection,
                    task_id=row["task_id"],
                    event_name="tool.error.persisted",
                    recorded_at=recorded_at,
                    input_data={"request_id": request_id, "tool_name": row["tool_name"]},
                    output_data={"error": error},
                    failure=error,
                )

    def _save_output(
        self,
        task_id: str,
        output_type: str,
        payload: dict[str, Any],
        *,
        trace_event_name: str | None = None,
        trace_input: dict[str, Any] | None = None,
    ) -> None:
        with self._transaction() as connection:
            recorded_at = utc_now()
            connection.execute(
                "INSERT INTO outputs(task_id, output_type, output_json, recorded_at_utc) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(task_id) DO UPDATE SET output_type=excluded.output_type, output_json=excluded.output_json, recorded_at_utc=excluded.recorded_at_utc",
                (task_id, output_type, _json(payload), recorded_at.isoformat()),
            )
            if trace_event_name is not None:
                self._append_trace_step(
                    connection,
                    task_id=task_id,
                    event_name=trace_event_name,
                    recorded_at=recorded_at,
                    input_data=trace_input or {},
                    output_data=payload,
                    model_id=(str(payload["model_id"]) if payload.get("model_id") else None),
                )

    def _append_trace_step(
        self,
        connection: sqlite3.Connection,
        *,
        task_id: str,
        event_name: str,
        recorded_at: datetime,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        failure: dict[str, Any] | None = None,
        model_id: str | None = None,
    ) -> None:
        run_row = connection.execute(
            "SELECT * FROM trace_runs WHERE task_id=?",
            (task_id,),
        ).fetchone()
        if run_row is None:
            return
        last = connection.execute(
            "SELECT ordinal, step_hash FROM trace_steps WHERE run_id=? ORDER BY ordinal DESC LIMIT 1",
            (run_row["run_id"],),
        ).fetchone()
        ordinal = int(last["ordinal"]) + 1 if last is not None else 0
        previous_hash = str(last["step_hash"]) if last is not None else GENESIS_HASH
        step_id = stable_step_id(run_row["run_id"], ordinal, event_name)
        actor, component = actor_component(event_name)
        determinism = classify_event(event_name)
        input_hash = hash_payload(input_data)
        output_hash = hash_payload(output_data)
        semantic_digest = semantic_hash(event_name, input_data, output_data)
        state_from = (
            str(output_data["from_state"])
            if output_data.get("from_state") is not None
            else None
        )
        state_to = (
            str(output_data["to_state"])
            if output_data.get("to_state") is not None
            else None
        )
        resolved_model = model_id
        if resolved_model is None and output_data.get("model_id") is not None:
            resolved_model = str(output_data["model_id"])
        if resolved_model is None:
            resolved_model = run_row["model_id"]
        resolved_failure = failure
        if resolved_failure is None and output_data.get("error_code") is not None:
            resolved_failure = {
                "error_code": output_data.get("error_code"),
                "error_details": output_data.get("error_details", {}),
            }
        recorded_at_utc = recorded_at.isoformat()
        step_hash = compute_step_hash(
            run_id=run_row["run_id"],
            ordinal=ordinal,
            step_id=step_id,
            recorded_at_utc=recorded_at_utc,
            actor=actor,
            component=component,
            event_name=event_name,
            determinism=determinism.value,
            input_hash=input_hash,
            output_hash=output_hash,
            semantic_digest=semantic_digest,
            state_from=state_from,
            state_to=state_to,
            model_id=resolved_model,
            configuration_hash=run_row["configuration_hash"],
            failure=resolved_failure,
            previous_hash=previous_hash,
        )
        connection.execute(
            """
            INSERT INTO trace_steps(
                run_id, ordinal, step_id, recorded_at_utc, actor, component,
                event_name, determinism, input_json, input_hash, output_json,
                output_hash, semantic_hash, state_from, state_to, model_id,
                configuration_hash, failure_json, previous_hash, step_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_row["run_id"],
                ordinal,
                step_id,
                recorded_at_utc,
                actor,
                component,
                event_name,
                determinism.value,
                _json(input_data),
                input_hash,
                _json(output_data),
                output_hash,
                semantic_digest,
                state_from,
                state_to,
                resolved_model,
                run_row["configuration_hash"],
                _json(resolved_failure) if resolved_failure is not None else None,
                previous_hash,
                step_hash,
            ),
        )
        status = run_row["status"]
        finished_at = run_row["finished_at_utc"]
        if event_name == "task.completed":
            status = "completed"
            finished_at = recorded_at_utc
        elif event_name == "task.failed":
            status = "failed"
            finished_at = recorded_at_utc
        connection.execute(
            "UPDATE trace_runs SET status=?, finished_at_utc=?, model_id=COALESCE(?, model_id), final_chain_hash=? WHERE run_id=?",
            (status, finished_at, resolved_model, step_hash, run_row["run_id"]),
        )

    @staticmethod
    def _trace_run(row: sqlite3.Row) -> TraceRun:
        return TraceRun(
            run_id=row["run_id"],
            task_id=row["task_id"],
            started_at=_datetime(row["started_at_utc"]),
            finished_at=(
                _datetime(row["finished_at_utc"])
                if row["finished_at_utc"] is not None
                else None
            ),
            status=row["status"],
            model_id=row["model_id"],
            configuration_hash=row["configuration_hash"],
            final_chain_hash=row["final_chain_hash"],
            source_run_id=row["source_run_id"],
            metadata=_mapping(row["metadata_json"]),
        )

    def trace_run_for_task(self, task_id: str) -> TraceRun:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM trace_runs WHERE task_id=?", (task_id,)
            ).fetchone()
        if row is None:
            raise TaskNotFoundError(
                "trace run does not exist for task",
                details={"task_id": task_id},
            )
        return self._trace_run(row)

    def load_trace_run(self, run_id: str) -> TraceRun:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM trace_runs WHERE run_id=?", (run_id,)
            ).fetchone()
        if row is None:
            raise TaskNotFoundError(
                "trace run does not exist",
                details={"run_id": run_id},
            )
        return self._trace_run(row)

    def list_trace_runs(self) -> tuple[TraceRun, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_runs ORDER BY started_at_utc, run_id"
            ).fetchall()
        return tuple(self._trace_run(row) for row in rows)

    def trace_steps(self, run_id: str) -> tuple[TraceStep, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_steps WHERE run_id=? ORDER BY ordinal",
                (run_id,),
            ).fetchall()
        return tuple(
            TraceStep(
                run_id=row["run_id"],
                ordinal=int(row["ordinal"]),
                step_id=row["step_id"],
                recorded_at=_datetime(row["recorded_at_utc"]),
                actor=row["actor"],
                component=row["component"],
                event_name=row["event_name"],
                determinism=DeterminismClass(row["determinism"]),
                input_data=_mapping(row["input_json"]),
                input_hash=row["input_hash"],
                output_data=_mapping(row["output_json"]),
                output_hash=row["output_hash"],
                semantic_hash=row["semantic_hash"],
                state_from=row["state_from"],
                state_to=row["state_to"],
                model_id=row["model_id"],
                configuration_hash=row["configuration_hash"],
                failure=(
                    _mapping(row["failure_json"])
                    if row["failure_json"] is not None
                    else None
                ),
                previous_hash=row["previous_hash"],
                step_hash=row["step_hash"],
            )
            for row in rows
        )

    def save_trace_replay(self, report: ReplayReport) -> None:
        with self._transaction() as connection:
            connection.execute(
                "INSERT INTO trace_replays(replay_id, source_run_id, started_at_utc, finished_at_utc, status, report_json) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    report.replay_id,
                    report.source_run_id,
                    report.started_at.isoformat(),
                    report.finished_at.isoformat(),
                    report.status,
                    _json(report.as_dict()),
                ),
            )

    def observability_data(
        self,
        *,
        since: datetime,
        recent_task_limit: int,
        recent_event_limit: int,
    ) -> dict[str, Any]:
        """Return one consistent SQLite snapshot for Stage 12 aggregation."""

        since_utc = since.isoformat()
        with self._connection() as connection:
            connection.execute("BEGIN")
            task_total = int(
                connection.execute(
                    "SELECT COUNT(*) FROM tasks WHERE updated_at_utc>=?",
                    (since_utc,),
                ).fetchone()[0]
            )
            state_rows = connection.execute(
                "SELECT COALESCE(current_state, 'unknown') AS state, COUNT(*) AS count "
                "FROM tasks WHERE updated_at_utc>=? GROUP BY current_state",
                (since_utc,),
            ).fetchall()
            event_rows = connection.execute(
                "SELECT name, COUNT(*) AS count FROM metric_events "
                "WHERE recorded_at_utc>=? GROUP BY name",
                (since_utc,),
            ).fetchall()
            tool_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM tool_calls WHERE started_at_utc>=?",
                    (since_utc,),
                ).fetchone()[0]
            )
            recovery_rows = connection.execute(
                "SELECT * FROM recovery_attempts WHERE started_at_utc>=? ORDER BY attempt_id",
                (since_utc,),
            ).fetchall()
            trace_run_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM trace_runs tr JOIN tasks t ON t.task_id=tr.task_id WHERE t.updated_at_utc>=?",
                    (since_utc,),
                ).fetchone()[0]
            )
            trace_step_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM trace_steps ts JOIN trace_runs tr ON tr.run_id=ts.run_id "
                    "JOIN tasks t ON t.task_id=tr.task_id WHERE t.updated_at_utc>=?",
                    (since_utc,),
                ).fetchone()[0]
            )
            replay_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM trace_replays WHERE started_at_utc>=?",
                    (since_utc,),
                ).fetchone()[0]
            )
            aggregate_outputs = connection.execute(
                "SELECT o.task_id, o.output_type, o.output_json, o.recorded_at_utc "
                "FROM outputs o JOIN tasks t ON t.task_id=o.task_id "
                "WHERE t.updated_at_utc>=? ORDER BY o.recorded_at_utc",
                (since_utc,),
            ).fetchall()
            task_durations = connection.execute(
                "SELECT task_id, created_at_utc, updated_at_utc FROM tasks "
                "WHERE updated_at_utc>=? ORDER BY updated_at_utc",
                (since_utc,),
            ).fetchall()
            tool_samples = connection.execute(
                "SELECT task_id, started_at_utc, finished_at_utc, status FROM tool_calls "
                "WHERE started_at_utc>=? ORDER BY started_at_utc",
                (since_utc,),
            ).fetchall()
            scheduler_samples = connection.execute(
                "SELECT task_id, recorded_at_utc, attributes_json FROM metric_events "
                "WHERE recorded_at_utc>=? AND name='scheduler.request.completed' "
                "ORDER BY metric_id",
                (since_utc,),
            ).fetchall()
            recent_events = connection.execute(
                "SELECT name, recorded_at_utc, task_id, attributes_json FROM metric_events "
                "WHERE recorded_at_utc>=? ORDER BY metric_id DESC LIMIT ?",
                (since_utc, recent_event_limit),
            ).fetchall()
            task_rows = connection.execute(
                """
                SELECT t.*, tr.run_id, tr.model_id AS trace_model_id,
                       (SELECT COUNT(*) FROM trace_steps ts WHERE ts.run_id=tr.run_id) AS trace_step_count,
                       o.output_type, o.output_json, o.recorded_at_utc AS output_recorded_at_utc
                FROM tasks t
                LEFT JOIN trace_runs tr ON tr.task_id=t.task_id
                LEFT JOIN outputs o ON o.task_id=t.task_id
                WHERE t.updated_at_utc>=?
                ORDER BY t.updated_at_utc DESC, t.task_id
                LIMIT ?
                """,
                (since_utc, recent_task_limit),
            ).fetchall()
            recent_tasks: list[dict[str, Any]] = []
            for task_row in task_rows:
                task_id = task_row["task_id"]
                task_events = connection.execute(
                    "SELECT name, recorded_at_utc, attributes_json FROM metric_events "
                    "WHERE task_id=? ORDER BY metric_id",
                    (task_id,),
                ).fetchall()
                task_tools = connection.execute(
                    "SELECT request_id, tool_name, status, started_at_utc, finished_at_utc "
                    "FROM tool_calls WHERE task_id=? ORDER BY started_at_utc",
                    (task_id,),
                ).fetchall()
                task_recoveries = connection.execute(
                    "SELECT attempt_id, checkpoint_phase, status, started_at_utc, finished_at_utc, details_json "
                    "FROM recovery_attempts WHERE task_id=? ORDER BY attempt_id",
                    (task_id,),
                ).fetchall()
                recent_tasks.append(
                    {
                        "task": dict(task_row),
                        "events": [
                            {
                                "name": row["name"],
                                "recorded_at_utc": row["recorded_at_utc"],
                                "attributes": _mapping(row["attributes_json"]),
                            }
                            for row in task_events
                        ],
                        "tools": [dict(row) for row in task_tools],
                        "recoveries": [
                            {
                                **dict(row),
                                "details": _mapping(row["details_json"]),
                            }
                            for row in task_recoveries
                        ],
                    }
                )
        return {
            "task_total": task_total,
            "task_states": {row["state"]: int(row["count"]) for row in state_rows},
            "event_counts": {row["name"]: int(row["count"]) for row in event_rows},
            "tool_count": tool_count,
            "recoveries": [
                {
                    **dict(row),
                    "details": _mapping(row["details_json"]),
                }
                for row in recovery_rows
            ],
            "trace_run_count": trace_run_count,
            "trace_step_count": trace_step_count,
            "replay_count": replay_count,
            "aggregate_outputs": [
                {
                    "task_id": row["task_id"],
                    "output_type": row["output_type"],
                    "payload": _mapping(row["output_json"]),
                    "recorded_at_utc": row["recorded_at_utc"],
                }
                for row in aggregate_outputs
            ],
            "task_durations": [dict(row) for row in task_durations],
            "tool_samples": [dict(row) for row in tool_samples],
            "scheduler_samples": [
                {
                    "task_id": row["task_id"],
                    "recorded_at_utc": row["recorded_at_utc"],
                    "attributes": _mapping(row["attributes_json"]),
                }
                for row in scheduler_samples
            ],
            "recent_events": [
                {
                    "name": row["name"],
                    "recorded_at_utc": row["recorded_at_utc"],
                    "task_id": row["task_id"],
                    "attributes": _mapping(row["attributes_json"]),
                }
                for row in recent_events
            ],
            "recent_tasks": recent_tasks,
        }

    def recovery_candidate(self, task_id: str) -> RecoveryCandidate:
        task = self.load_task(task_id)
        state = self.current(task_id)
        checkpoint = self.latest(task_id)
        if state in TERMINAL_STATES:
            return RecoveryCandidate(task, state, checkpoint, RecoveryDisposition.TERMINAL, "terminal tasks are never retried")
        if state is not TaskState.PLANNING:
            return RecoveryCandidate(task, state, checkpoint, RecoveryDisposition.UNSAFE_TO_RETRY, "only pre-invocation PLANNING checkpoints are supported")
        if checkpoint is None or checkpoint.phase != "recovery_ready" or not checkpoint.data.get("safe_to_retry"):
            return RecoveryCandidate(task, state, checkpoint, RecoveryDisposition.INVALID_CHECKPOINT, "latest checkpoint is not an explicit recovery_ready boundary")
        return RecoveryCandidate(task, state, checkpoint, RecoveryDisposition.RECOVERABLE, "checkpoint precedes all model and tool invocation side effects")

    def begin_recovery(self, task_id: str, checkpoint_phase: str) -> int:
        with self._transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO recovery_attempts(task_id, checkpoint_phase, status, started_at_utc, details_json) VALUES (?, ?, 'running', ?, '{}')",
                (task_id, checkpoint_phase, utc_now().isoformat()),
            )
            return int(cursor.lastrowid)

    def finish_recovery(self, attempt_id: int, status: str, details: dict[str, Any]) -> None:
        with self._transaction() as connection:
            connection.execute(
                "UPDATE recovery_attempts SET status=?, finished_at_utc=?, details_json=? WHERE attempt_id=?",
                (status, utc_now().isoformat(), _json(details), attempt_id),
            )

    def table_counts(self) -> dict[str, int]:
        tables = ("agents", "tasks", "state_transitions", "checkpoints", "lifecycle_events", "metric_events", "execution_steps", "model_configurations", "tool_calls", "outputs", "recovery_attempts", "trace_runs", "trace_steps", "trace_replays")
        with self._connection() as connection:
            return {table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}

    def integrity_check(self) -> str:
        with self._connection() as connection:
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])
