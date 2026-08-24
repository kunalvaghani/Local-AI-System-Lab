import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.errors import DuplicateAgentError, IllegalStateTransitionError, RecoveryNotSupportedError
from runtime.factory import build_stage10_runtime, build_stage10_stub_runtime
from runtime.models import Agent, Task, TaskState
from runtime.persistence import PersistenceConfig, RecoveryDisposition, SQLiteRuntimeStore
from runtime.recovery_cli import main as recovery_main


class SQLiteSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "runtime.db"
        self.config = PersistenceConfig(self.path)

    def test_schema_is_versioned_idempotent_and_healthy(self) -> None:
        first = SQLiteRuntimeStore(self.config)
        second = SQLiteRuntimeStore(self.config)
        self.assertEqual(first.schema_version, 2)
        self.assertEqual(second.schema_version, 2)
        self.assertEqual(second.integrity_check(), "ok")
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0], 2)

    def test_newer_schema_is_rejected(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at_utc TEXT NOT NULL)")
            connection.execute("INSERT INTO schema_migrations VALUES (99, 'future')")
        with self.assertRaises(sqlite3.DatabaseError):
            SQLiteRuntimeStore(self.config)

    def test_illegal_transition_rolls_back_without_partial_state(self) -> None:
        store = SQLiteRuntimeStore(self.config)
        task = Task.create(agent_id="agent", objective="transaction test")
        store.save_task(task)
        store.initialize(task.task_id, reason="created")
        with self.assertRaises(IllegalStateTransitionError):
            store.transition(task.task_id, TaskState.COMPLETED, reason="illegal")
        self.assertEqual(store.current(task.task_id), TaskState.CREATED)
        self.assertEqual(len(store.history(task.task_id)), 1)

    def test_conflicting_agent_snapshot_is_rejected(self) -> None:
        store = SQLiteRuntimeStore(self.config)
        store.ensure_agent(TECHNICAL_EXPLAINER)
        changed = Agent(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            name="Changed",
            objective=TECHNICAL_EXPLAINER.objective,
        )
        with self.assertRaises(DuplicateAgentError):
            store.ensure_agent(changed)


class DurableRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "runtime.db"

    def runtime(self):
        runtime = build_stage10_stub_runtime(self.path)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        return runtime

    def test_inference_task_persists_every_required_record_family(self) -> None:
        runtime = self.runtime()
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        counts = runtime.components.persistence.table_counts()  # type: ignore[union-attr]
        self.assertEqual(runtime.components.persistence.integrity_check(), "ok")  # type: ignore[union-attr]
        for table in (
            "agents", "tasks", "state_transitions", "checkpoints",
            "lifecycle_events", "metric_events", "execution_steps",
            "model_configurations", "outputs",
        ):
            self.assertGreater(counts[table], 0, table)
        self.assertEqual(runtime.task_state(result.task_id), TaskState.COMPLETED)
        with sqlite3.connect(self.path) as connection:
            output = json.loads(connection.execute("SELECT output_json FROM outputs WHERE task_id=?", (result.task_id,)).fetchone()[0])
        self.assertEqual(output["output"], result.output)

    def test_tool_request_result_and_output_are_durable(self) -> None:
        runtime = self.runtime()
        result = runtime.run_tool(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 80},
        )
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT status, result_json FROM tool_calls WHERE request_id=?", (result.request_id,)).fetchone()
            output_type = connection.execute("SELECT output_type FROM outputs WHERE task_id=?", (result.task_id,)).fetchone()[0]
        self.assertEqual(row[0], "completed")
        self.assertTrue(json.loads(row[1])["success"])
        self.assertEqual(output_type, "tool")

    def test_restart_reconstructs_task_state_history_and_events(self) -> None:
        first = self.runtime()
        result = first.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        first.shutdown()
        second = self.runtime()
        self.assertEqual(second.task_state(result.task_id), TaskState.COMPLETED)
        self.assertEqual([item.to_state for item in second.state_history(result.task_id)], [TaskState.CREATED, TaskState.PLANNING, TaskState.EXECUTING, TaskState.VALIDATING, TaskState.COMPLETED])
        self.assertIn("task.completed", [event.name for event in second.components.events.snapshot(result.task_id)])

    def test_recovery_continues_from_explicit_checkpoint(self) -> None:
        first = self.runtime()
        task = first.prepare_recoverable_task(agent_id=TECHNICAL_EXPLAINER.agent_id)
        first.shutdown()
        second = self.runtime()
        candidate = second.components.persistence.recovery_candidate(task.task_id)  # type: ignore[union-attr]
        self.assertEqual(candidate.disposition, RecoveryDisposition.RECOVERABLE)
        result = second.recover_task(task.task_id)
        self.assertEqual(result.final_state, TaskState.COMPLETED)
        self.assertEqual([item.to_state for item in result.state_history], [TaskState.CREATED, TaskState.PLANNING, TaskState.RECOVERING, TaskState.PLANNING, TaskState.EXECUTING, TaskState.VALIDATING, TaskState.COMPLETED])
        self.assertEqual(second.components.inference.call_count, 1)  # type: ignore[attr-defined]
        self.assertEqual(second.components.persistence.table_counts()["recovery_attempts"], 1)  # type: ignore[union-attr]

    def test_terminal_and_inflight_tasks_are_not_retried(self) -> None:
        runtime = self.runtime()
        completed = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        with self.assertRaises(RecoveryNotSupportedError):
            runtime.recover_task(completed.task_id)
        prepared = runtime.prepare_recoverable_task(agent_id=TECHNICAL_EXPLAINER.agent_id)
        runtime.components.state_machine.transition(prepared.task_id, TaskState.EXECUTING, reason="simulate crash after invocation boundary")
        candidate = runtime.components.persistence.recovery_candidate(prepared.task_id)  # type: ignore[union-attr]
        self.assertEqual(candidate.disposition, RecoveryDisposition.UNSAFE_TO_RETRY)
        with self.assertRaises(RecoveryNotSupportedError):
            runtime.recover_task(prepared.task_id)
        self.assertEqual(runtime.components.inference.call_count, 1)  # type: ignore[attr-defined]

    def test_real_stage10_factory_composes_sqlite_without_starting_model(self) -> None:
        runtime = build_stage10_runtime(database_path=self.path)
        self.assertIsNotNone(runtime.components.persistence)
        self.assertEqual(runtime.components.persistence.schema_version, 2)  # type: ignore[union-attr]
        self.assertEqual(len(runtime.available_agents()), 2)


class RecoveryCliTests(unittest.TestCase):
    def test_cli_kills_worker_and_recovers_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = StringIO()
            with redirect_stdout(output):
                code = recovery_main(["--db", str(Path(folder) / "recovery.db")])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertNotEqual(payload["interruption"]["exit_code"], 0)
        self.assertEqual(payload["interruption"]["state_before_kill"], "planning")
        self.assertEqual(payload["restart"]["final_state"], "completed")
        self.assertEqual(payload["restart"]["state_history"][2], "recovering")
        self.assertEqual(payload["restart"]["real_llm_calls"], 0)
        self.assertEqual(payload["database_evidence"]["integrity_check"], "ok")


if __name__ == "__main__":
    unittest.main()
