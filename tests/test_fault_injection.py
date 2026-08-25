import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.chaos_cli import main as chaos_main
from runtime.errors import (
    ConfigurationError,
    ContextOverflowError,
    DatabaseOperationError,
    InvalidOutputError,
    ModelOutOfMemoryError,
    TaskTimeoutError,
    ToolArgumentValidationError,
)
from runtime.factory import build_stage13_runtime, build_stage13_stub_runtime
from runtime.faults import FaultKind, load_chaos_config
from runtime.models import TaskState


class ChaosConfigurationTests(unittest.TestCase):
    def test_configuration_is_disabled_bounded_and_selectable(self) -> None:
        config = load_chaos_config()
        self.assertFalse(config.enabled)
        self.assertEqual(len(config.scenarios), 9)
        self.assertFalse(config.plan().armed)
        armed = config.plan(armed=True, scenario_ids=("model-timeout",))
        self.assertTrue(armed.armed)
        self.assertEqual(armed.scenarios[0].kind, FaultKind.MODEL_TIMEOUT)
        with self.assertRaises(ConfigurationError):
            config.plan(armed=True, scenario_ids=("missing",))

    def test_configuration_rejects_unbounded_or_mistyped_values(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "chaos.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "enabled": False,
                        "max_delay_ms": 10,
                        "scenarios": [
                            {
                                "scenario_id": "too-slow",
                                "kind": "model_timeout",
                                "delay_ms": 11,
                                "max_injections": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError):
                load_chaos_config(path)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "enabled": "yes",
                        "max_delay_ms": 10,
                        "scenarios": [
                            {
                                "scenario_id": "typed",
                                "kind": "model_timeout",
                                "delay_ms": 0,
                                "max_injections": 1,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError):
                load_chaos_config(path)


class FaultAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)

    def path(self, name: str) -> Path:
        return Path(self.folder.name) / f"{name}.db"

    def test_default_stage13_factory_is_inert(self) -> None:
        runtime = build_stage13_stub_runtime(self.path("inert"))
        runtime.start()
        self.addCleanup(runtime.shutdown)
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(result.final_state, TaskState.COMPLETED)
        self.assertFalse(runtime.components.faults.armed)  # type: ignore[union-attr]
        self.assertEqual(runtime.components.faults.snapshot(), tuple())  # type: ignore[union-attr]
        report = runtime.components.observability.report(include_live=False)  # type: ignore[union-attr]
        self.assertEqual(report.totals["fault_injections"], 0)

    def test_inference_faults_map_to_exact_terminal_states(self) -> None:
        cases = (
            ("model-timeout", TaskTimeoutError, TaskState.TIMEOUT),
            ("invalid-model-output", InvalidOutputError, TaskState.INVALID_OUTPUT),
            ("context-overflow", ContextOverflowError, TaskState.CONTEXT_OVERFLOW),
            ("simulated-oom", ModelOutOfMemoryError, TaskState.OUT_OF_MEMORY),
        )
        for scenario_id, error_type, state in cases:
            with self.subTest(scenario=scenario_id):
                runtime = build_stage13_stub_runtime(
                    self.path(scenario_id),
                    arm_faults=True,
                    scenario_ids=(scenario_id,),
                )
                runtime.start()
                try:
                    with self.assertRaises(error_type):
                        runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
                    record = runtime.components.faults.snapshot()[0]  # type: ignore[union-attr]
                    self.assertEqual(runtime.task_state(record.task_id), state)
                    self.assertEqual(len(runtime.components.faults.snapshot()), 1)  # type: ignore[union-attr]
                    report = runtime.components.observability.report(include_live=False)  # type: ignore[union-attr]
                    self.assertEqual(report.totals["fault_injections"], 1)
                finally:
                    runtime.shutdown()

    def test_injection_count_is_bounded_and_next_task_runs_normally(self) -> None:
        runtime = build_stage13_stub_runtime(
            self.path("bounded"),
            arm_faults=True,
            scenario_ids=("model-timeout",),
        )
        runtime.start()
        self.addCleanup(runtime.shutdown)
        with self.assertRaises(TaskTimeoutError):
            runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        second = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(second.final_state, TaskState.COMPLETED)
        self.assertEqual(len(runtime.components.faults.snapshot()), 1)  # type: ignore[union-attr]
        self.assertEqual(runtime.components.inference.call_count, 1)  # type: ignore[attr-defined]

    def test_tool_faults_map_to_exact_validation_and_timeout_states(self) -> None:
        cases = (
            ("tool-timeout", TaskTimeoutError, TaskState.TIMEOUT),
            ("corrupted-tool-result", InvalidOutputError, TaskState.INVALID_OUTPUT),
            ("malformed-tool-call", ToolArgumentValidationError, TaskState.TOOL_FAILED),
        )
        for scenario_id, error_type, state in cases:
            with self.subTest(scenario=scenario_id):
                runtime = build_stage13_stub_runtime(
                    self.path(scenario_id),
                    arm_faults=True,
                    scenario_ids=(scenario_id,),
                )
                runtime.start()
                try:
                    with self.assertRaises(error_type):
                        runtime.run_tool(
                            agent_id=TECHNICAL_EXPLAINER.agent_id,
                            tool_name="project_context_read",
                            arguments={"relative_path": "README.md", "max_characters": 80},
                        )
                    record = runtime.components.faults.snapshot()[0]  # type: ignore[union-attr]
                    self.assertEqual(runtime.task_state(record.task_id), state)
                finally:
                    runtime.shutdown()

    def test_database_fault_reproduces_terminal_output_atomicity_gap(self) -> None:
        path = self.path("database")
        runtime = build_stage13_stub_runtime(
            path,
            arm_faults=True,
            scenario_ids=("database-result-failure",),
        )
        runtime.start()
        self.addCleanup(runtime.shutdown)
        with self.assertRaises(DatabaseOperationError):
            runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        record = runtime.components.faults.snapshot()[0]  # type: ignore[union-attr]
        self.assertEqual(runtime.task_state(record.task_id), TaskState.COMPLETED)
        with sqlite3.connect(path) as connection:
            output_count = connection.execute(
                "SELECT COUNT(*) FROM outputs WHERE task_id=?",
                (record.task_id,),
            ).fetchone()[0]
        self.assertEqual(output_count, 0)

    def test_real_factory_composes_inert_faults_without_starting_model(self) -> None:
        runtime = build_stage13_runtime(database_path=self.path("real"))
        self.assertIsNotNone(runtime.components.faults)
        self.assertFalse(runtime.components.faults.armed)  # type: ignore[union-attr]
        self.assertEqual(runtime.components.persistence.schema_version, 2)  # type: ignore[union-attr]


class ChaosCliTests(unittest.TestCase):
    def test_cli_requires_explicit_arming(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unarmed.db"
            stderr = StringIO()
            with redirect_stderr(stderr):
                code = chaos_main(["--database", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("disabled", json.loads(stderr.getvalue())["message"])
            self.assertFalse(path.exists())

    def test_cli_model_timeout_report_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = StringIO()
            with redirect_stdout(output):
                code = chaos_main(
                    [
                        "--execute",
                        "--database",
                        str(Path(folder) / "single.db"),
                        "--scenario",
                        "model-timeout",
                    ]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(payload["armed"])
            self.assertEqual(payload["summary"]["injections"], 1)
            self.assertEqual(payload["summary"]["expected_outcome_rate_percent"], 100.0)
            self.assertEqual(payload["scenarios"][0]["actual"]["state"], "timeout")
            self.assertEqual(payload["database_integrity"], "ok")

    def test_real_process_termination_recovers_from_safe_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = StringIO()
            with redirect_stdout(output):
                code = chaos_main(
                    [
                        "--execute",
                        "--database",
                        str(Path(folder) / "crash.db"),
                        "--scenario",
                        "agent-crash-recovery",
                    ]
                )
            payload = json.loads(output.getvalue())
            scenario = payload["scenarios"][0]
            self.assertEqual(code, 0)
            self.assertNotEqual(scenario["details"]["worker_exit_code"], 0)
            self.assertEqual(scenario["details"]["state_before_termination"], "planning")
            self.assertEqual(scenario["actual"]["state"], "completed")
            self.assertTrue(scenario["recovery"]["succeeded"])
            self.assertEqual(payload["summary"]["recovery_success_rate_percent"], 100.0)
            self.assertEqual(payload["summary"]["real_llm_calls"], 0)


if __name__ == "__main__":
    unittest.main()
