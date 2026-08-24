import json
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path

from runtime.agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from runtime.errors import ConfigurationError, LabError, ValidationError
from runtime.factory import build_stage12_runtime, build_stage12_stub_runtime
from runtime.observability import ObservabilityConfig, distribution, load_observability_config
from runtime.observability_cli import main as observability_main


class ObservabilityModelTests(unittest.TestCase):
    def test_distribution_reports_linear_percentiles_and_missing_values(self) -> None:
        measured = distribution([100.0, 300.0], "ms")
        self.assertEqual(measured.count, 2)
        self.assertEqual(measured.p50, 200.0)
        self.assertEqual(measured.p95, 290.0)
        self.assertEqual(measured.mean, 200.0)
        missing = distribution([None, None], "MiB")
        self.assertEqual(missing.count, 0)
        self.assertIsNone(missing.p95)

    def test_configuration_and_report_limits_are_validated(self) -> None:
        with self.assertRaises(ConfigurationError):
            ObservabilityConfig(default_window_minutes=0)
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "bad.json"
            bad.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_observability_config(bad)
            bad.write_text(
                json.dumps({"schema_version": 1, "recent_task_limit": "50"}),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError):
                load_observability_config(bad)
            runtime = build_stage12_stub_runtime(Path(folder) / "runtime.db")
            runtime.start()
            try:
                with self.assertRaises(ValidationError):
                    runtime.components.observability.report(window_minutes=-1)  # type: ignore[union-attr]
                with self.assertRaises(ValidationError):
                    runtime.components.observability.report(recent_task_limit=0)  # type: ignore[union-attr]
            finally:
                runtime.shutdown()


class UnifiedObservabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "observability.db"

    def runtime(self):
        runtime = build_stage12_stub_runtime(self.path)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        return runtime

    def test_empty_report_has_no_fabricated_measurements(self) -> None:
        runtime = self.runtime()
        report = runtime.components.observability.report(include_live=False)  # type: ignore[union-attr]
        self.assertEqual(report.totals["tasks"], 0)
        self.assertIsNone(report.totals["completion_rate_percent"])
        self.assertEqual(report.distributions["ttft_ms"].count, 0)
        self.assertIsNone(report.distributions["ttft_ms"].p95)
        self.assertIsNone(report.live_scheduler)
        self.assertIsNone(report.live_hardware)

    def test_report_unifies_inference_tool_failure_recovery_and_trace_activity(self) -> None:
        runtime = self.runtime()
        inference = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        tool = runtime.run_tool(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 20},
        )
        with self.assertRaises(LabError):
            runtime.run_tool(
                agent_id=RISK_ANALYST.agent_id,
                tool_name="project_context_read",
                arguments={"relative_path": "README.md", "max_characters": 20},
            )
        prepared = runtime.prepare_recoverable_task(agent_id=TECHNICAL_EXPLAINER.agent_id)
        recovered = runtime.recover_task(prepared.task_id)
        report = runtime.components.observability.report(include_live=False)  # type: ignore[union-attr]
        self.assertEqual(report.totals["tasks"], 4)
        self.assertEqual(report.totals["completed_tasks"], 3)
        self.assertEqual(report.totals["failed_tasks"], 1)
        self.assertEqual(report.totals["model_calls_started"], 2)
        self.assertEqual(report.totals["tool_calls"], 1)
        self.assertEqual(report.totals["router_decisions"], 2)
        self.assertEqual(report.totals["recoveries"], 1)
        self.assertEqual(report.totals["retries"], 1)
        self.assertEqual(report.task_states["security_blocked"], 1)
        by_id = {task.task_id: task for task in report.recent_tasks}
        self.assertEqual(by_id[inference.task_id].model_calls, 1)
        self.assertEqual(by_id[tool.task_id].tool_calls, 1)
        self.assertEqual(by_id[recovered.task_id].recovery_attempts, 1)
        self.assertTrue(all(task.run_id for task in report.recent_tasks))
        failure = next(task for task in report.recent_tasks if task.failure)
        self.assertEqual(failure.failure["error_code"], "tool_permission_denied")  # type: ignore[index]

    def test_known_inference_samples_produce_expected_aggregates(self) -> None:
        runtime = self.runtime()
        first = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="first")
        second = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="second")
        with sqlite3.connect(self.path) as connection:
            for task_id, total, ttft, throughput, ram, vram in (
                (first.task_id, 100.0, 40.0, 10.0, 1000.0, 100.0),
                (second.task_id, 300.0, 80.0, 30.0, 1200.0, 200.0),
            ):
                row = connection.execute(
                    "SELECT output_json FROM outputs WHERE task_id=?", (task_id,)
                ).fetchone()
                payload = json.loads(row[0])
                payload["metrics"].update(
                    {
                        "total_ms": total,
                        "ttft_ms": ttft,
                        "tokens_per_second": throughput,
                        "peak_process_ram_mib": ram,
                        "vram_delta_mib": vram,
                    }
                )
                connection.execute(
                    "UPDATE outputs SET output_json=? WHERE task_id=?",
                    (json.dumps(payload), task_id),
                )
        report = runtime.components.observability.report(include_live=False)  # type: ignore[union-attr]
        self.assertEqual(report.distributions["inference_total_ms"].p50, 200.0)
        self.assertEqual(report.distributions["inference_total_ms"].p95, 290.0)
        self.assertEqual(report.distributions["ttft_ms"].p50, 60.0)
        self.assertEqual(report.distributions["generation_tokens_per_second"].mean, 20.0)
        self.assertEqual(report.distributions["peak_process_ram_mib"].maximum, 1200.0)
        self.assertEqual(report.distributions["vram_delta_mib"].maximum, 200.0)

    def test_recent_limit_does_not_change_window_totals_and_window_is_enforced(self) -> None:
        runtime = self.runtime()
        old = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="old")
        current = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="current")
        limited = runtime.components.observability.report(  # type: ignore[union-attr]
            recent_task_limit=1,
            recent_event_limit=2,
            include_live=False,
        )
        self.assertEqual(limited.totals["tasks"], 2)
        self.assertEqual(len(limited.recent_tasks), 1)
        self.assertEqual(len(limited.recent_events), 2)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE tasks SET created_at_utc='2000-01-01T00:00:00+00:00', updated_at_utc='2000-01-01T00:00:01+00:00' WHERE task_id=?",
                (old.task_id,),
            )
        windowed = runtime.components.observability.report(window_minutes=1, include_live=False)  # type: ignore[union-attr]
        self.assertEqual(windowed.totals["tasks"], 1)
        self.assertEqual(windowed.recent_tasks[0].task_id, current.task_id)

    def test_live_report_contains_scheduler_and_source_labelled_hardware(self) -> None:
        runtime = self.runtime()
        runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        report = runtime.components.observability.report(include_live=True)  # type: ignore[union-attr]
        self.assertEqual(report.live_scheduler["queue_depth"], 0)  # type: ignore[index]
        self.assertEqual(report.live_scheduler["submitted"], 1)  # type: ignore[index]
        self.assertIn("source", report.live_hardware["cpu"])  # type: ignore[index]
        self.assertIn("source", report.live_hardware["ram"])  # type: ignore[index]

    def test_real_factory_exposes_observability_without_starting_model(self) -> None:
        runtime = build_stage12_runtime(database_path=Path(self.folder.name) / "real.db")
        self.assertIsNotNone(runtime.components.observability)
        self.assertIsNotNone(runtime.components.traces)
        self.assertEqual(runtime.components.persistence.schema_version, 2)  # type: ignore[union-attr]


class ObservabilityCliTests(unittest.TestCase):
    def test_demo_and_existing_database_report_are_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "demo.db"
            output = StringIO()
            with redirect_stdout(output):
                code = observability_main(
                    ["demo", "--database", str(database), "--no-live", "--event-limit", "5"]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["stage"], 12)
            self.assertEqual(payload["report"]["totals"]["tasks"], 4)
            self.assertEqual(len(payload["report"]["recent_events"]), 5)
            with closing(sqlite3.connect(database)) as connection:
                events_before = connection.execute(
                    "SELECT COUNT(*) FROM metric_events"
                ).fetchone()[0]
            report_output = StringIO()
            with redirect_stdout(report_output):
                report_code = observability_main(
                    ["report", "--database", str(database), "--no-live", "--limit", "2"]
                )
            report_payload = json.loads(report_output.getvalue())
            self.assertEqual(report_code, 0)
            self.assertEqual(report_payload["report"]["totals"]["tasks"], 4)
            self.assertEqual(len(report_payload["report"]["recent_tasks"]), 2)
            with closing(sqlite3.connect(database)) as connection:
                events_after = connection.execute(
                    "SELECT COUNT(*) FROM metric_events"
                ).fetchone()[0]
            self.assertEqual(events_after, events_before)


if __name__ == "__main__":
    unittest.main()
