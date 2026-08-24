import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.factory import build_stage11_runtime, build_stage11_stub_runtime
from runtime.persistence import PersistenceConfig, SQLiteRuntimeStore
from runtime.trace_cli import main as trace_main
from runtime.tracing import (
    DeterminismClass,
    ReplayOutcome,
    SQLiteTraceStore,
    TraceReplayEngine,
    compare_traces,
)


class TraceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "trace.db"

    def runtime(self):
        runtime = build_stage11_stub_runtime(self.path)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        return runtime

    def test_schema_v2_is_idempotent_and_migrates_version_one(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at_utc TEXT NOT NULL)"
            )
            connection.execute("INSERT INTO schema_migrations VALUES (1, 'stage-10')")
        store = SQLiteRuntimeStore(PersistenceConfig(self.path))
        self.assertEqual(store.schema_version, 2)
        with sqlite3.connect(self.path) as connection:
            versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(versions, [1, 2])
        self.assertTrue({"trace_runs", "trace_steps", "trace_replays"}.issubset(tables))

    def test_completed_task_has_hash_chained_structured_trace(self) -> None:
        runtime = self.runtime()
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        traces = runtime.components.traces
        self.assertIsNotNone(traces)
        run = traces.for_task(result.task_id)  # type: ignore[union-attr]
        steps = tuple(traces.steps(run.run_id))  # type: ignore[union-attr]
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.final_chain_hash, steps[-1].step_hash)
        self.assertEqual([step.ordinal for step in steps], list(range(len(steps))))
        self.assertEqual(len({step.step_id for step in steps}), len(steps))
        self.assertTrue(all(len(step.input_hash) == 64 for step in steps))
        self.assertTrue(all(len(step.output_hash) == 64 for step in steps))
        model_start = next(step for step in steps if step.event_name == "model.invocation.started")
        model_end = next(step for step in steps if step.event_name == "model.invocation.completed")
        self.assertEqual(model_start.determinism, DeterminismClass.NONDETERMINISTIC)
        self.assertEqual(len(model_start.output_data["input_hash"]), 64)
        self.assertEqual(len(model_end.output_data["output_hash"]), 64)

    def test_replay_verifies_deterministic_steps_without_new_model_call(self) -> None:
        runtime = self.runtime()
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        before = runtime.components.inference.call_count  # type: ignore[attr-defined]
        traces = runtime.components.traces
        run = traces.for_task(result.task_id)  # type: ignore[union-attr]
        report = TraceReplayEngine(traces).replay(run.run_id)  # type: ignore[arg-type]
        self.assertTrue(report.integrity_valid)
        self.assertEqual(report.status, "matched")
        self.assertEqual(report.reconstructed_state, "completed")
        self.assertGreater(report.counts()[ReplayOutcome.MATCHED.value], 0)
        self.assertGreater(report.counts()[ReplayOutcome.OBSERVED_ONLY.value], 0)
        self.assertEqual(runtime.components.inference.call_count, before)  # type: ignore[attr-defined]
        self.assertEqual(runtime.components.persistence.table_counts()["trace_replays"], 1)  # type: ignore[union-attr]

    def test_tampered_payload_fails_integrity_replay(self) -> None:
        runtime = self.runtime()
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        traces = runtime.components.traces
        run = traces.for_task(result.task_id)  # type: ignore[union-attr]
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE trace_steps SET output_json=? WHERE run_id=? AND ordinal=0",
                (json.dumps({"tampered": True}), run.run_id),
            )
        report = TraceReplayEngine(traces).replay(run.run_id)  # type: ignore[arg-type]
        self.assertFalse(report.integrity_valid)
        self.assertEqual(report.status, "integrity_failed")
        self.assertIn(
            ReplayOutcome.INTEGRITY_FAILED,
            {step.outcome for step in report.steps},
        )

    def test_two_equivalent_runs_match_deterministic_semantics(self) -> None:
        objective = "Explain deterministic replay boundaries."
        runs = []
        traces = None
        for _ in range(2):
            runtime = self.runtime()
            result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective=objective)
            traces = runtime.components.traces
            runs.append(traces.for_task(result.task_id))  # type: ignore[union-attr]
            runtime.shutdown()
        comparison = compare_traces(
            runs[0], traces.steps(runs[0].run_id),  # type: ignore[union-attr]
            runs[1], traces.steps(runs[1].run_id),  # type: ignore[union-attr]
        )
        self.assertGreater(comparison.deterministic_matches, 0)
        self.assertEqual(comparison.deterministic_divergences, 0)
        self.assertGreater(comparison.nondeterministic_observations, 0)
        self.assertTrue(comparison.model_match)
        self.assertTrue(comparison.configuration_match)

    def test_different_objectives_produce_deterministic_divergence(self) -> None:
        runtime = self.runtime()
        first = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="Objective A")
        second = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="Objective B")
        traces = runtime.components.traces
        left = traces.for_task(first.task_id)  # type: ignore[union-attr]
        right = traces.for_task(second.task_id)  # type: ignore[union-attr]
        comparison = compare_traces(
            left, traces.steps(left.run_id), right, traces.steps(right.run_id)  # type: ignore[union-attr]
        )
        self.assertGreater(comparison.deterministic_divergences, 0)

    def test_tool_side_effect_boundaries_are_recorded_but_skipped(self) -> None:
        runtime = self.runtime()
        result = runtime.run_tool(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 40},
        )
        traces = runtime.components.traces
        run = traces.for_task(result.task_id)  # type: ignore[union-attr]
        steps = tuple(traces.steps(run.run_id))  # type: ignore[union-attr]
        self.assertIn(DeterminismClass.SIDE_EFFECTING, {step.determinism for step in steps})
        report = TraceReplayEngine(traces).replay(run.run_id)  # type: ignore[arg-type]
        self.assertGreater(report.counts()[ReplayOutcome.SKIPPED_SIDE_EFFECT.value], 0)

    def test_trace_survives_restart_and_real_factory_exposes_store(self) -> None:
        first = self.runtime()
        result = first.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        run_id = first.components.traces.for_task(result.task_id).run_id  # type: ignore[union-attr]
        first.shutdown()
        store = SQLiteTraceStore(SQLiteRuntimeStore(PersistenceConfig(self.path)))
        self.assertEqual(store.load_run(run_id).task_id, result.task_id)
        self.assertGreater(len(store.steps(run_id)), 0)
        real = build_stage11_runtime(database_path=Path(self.folder.name) / "real.db")
        self.assertIsNotNone(real.components.traces)
        self.assertEqual(real.components.persistence.schema_version, 2)  # type: ignore[union-attr]


class TraceCliTests(unittest.TestCase):
    def test_demo_loads_replays_and_compares_two_runs(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "demo.db"
            output = StringIO()
            with redirect_stdout(output):
                code = trace_main(["demo", "--database", str(database)])
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["stage"], 11)
            self.assertEqual(payload["schema_version"], 2)
            self.assertEqual(payload["integrity_check"], "ok")
            self.assertEqual(len(payload["runs"]), 2)
            self.assertTrue(payload["replay"]["integrity_valid"])
            self.assertEqual(payload["comparison"]["deterministic_divergences"], 0)
            left = payload["runs"][0]["run_id"]
            right = payload["runs"][1]["run_id"]
            for arguments, expected_key in (
                (["inspect", "--database", str(database), "--run-id", left], "trace"),
                (["replay", "--database", str(database), "--run-id", left], "replay"),
                (["compare", "--database", str(database), "--left-run-id", left, "--right-run-id", right], "comparison"),
            ):
                mode_output = StringIO()
                with redirect_stdout(mode_output):
                    self.assertEqual(trace_main(arguments), 0)
                self.assertIn(expected_key, json.loads(mode_output.getvalue()))


if __name__ == "__main__":
    unittest.main()
