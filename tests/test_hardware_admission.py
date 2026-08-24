import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from dataclasses import replace
from pathlib import Path

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.engine import AgentRuntime
from runtime.errors import AdmissionControlError, ConfigurationError
from runtime.factory import build_stage1_runtime, build_stage7_runtime
from runtime.hardware import (
    AdmissionAction,
    AdmissionPolicy,
    AdmissionRequest,
    Confidence,
    ConservativeMemoryEstimator,
    CpuSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    LocalHardwareProfiler,
    ModelMemoryProfile,
    RamSnapshot,
    load_admission_config,
)
from runtime.hardware_cli import controlled_decisions
from runtime.hardware_cli import main as hardware_main
from runtime.models import TaskState


def hardware(free_vram: float = 4000.0, total_vram: float = 4096.0) -> HardwareSnapshot:
    return HardwareSnapshot(
        CpuSnapshot("CPU", 16, 8, "test", Confidence.HIGH),
        RamSnapshot(32000.0, 12000.0, 20000.0, "test", Confidence.HIGH),
        GpuSnapshot("GPU", "1", total_vram, total_vram - free_vram, free_vram, 1, 40, "8.6", "test", Confidence.HIGH),
    )


class ProfilerAndEstimatorTests(unittest.TestCase):
    def test_profiler_reports_sources_and_parses_pressure(self) -> None:
        profiler = LocalHardwareProfiler(
            cpu_reader=lambda: ("Test CPU", 8, "cpu fixture"),
            memory_reader=lambda: (32 * 1024**3, 12 * 1024**3, "ram fixture"),
            gpu_runner=lambda: "Test GPU, 610.0, 4096, 1000, 3096, 25, 55, 8.6\n",
        )
        snapshot = profiler.snapshot()
        self.assertEqual(snapshot.cpu.physical_cores, 8)
        self.assertEqual(snapshot.ram.available_mib, 12288.0)
        self.assertEqual(snapshot.gpu.free_vram_mib, 3096.0)  # type: ignore[union-attr]
        self.assertEqual(snapshot.gpu.source, "nvidia-smi live query")  # type: ignore[union-attr]

    def test_config_uses_actual_model_file_and_estimate_compares_measurement(self) -> None:
        config = load_admission_config()
        self.assertAlmostEqual(
            config.model.file_size_mib,
            Path(config.model.path).stat().st_size / 1024**2,
        )
        estimator = ConservativeMemoryEstimator(config.estimator)
        request = AdmissionRequest(config.model, 2048, 28)
        comparison = estimator.compare_calibration(request, config.calibration)
        self.assertGreater(comparison.host_error_mib, 0)
        self.assertGreater(comparison.vram_error_mib, 0)
        self.assertLess(comparison.host_error_percent, 15)

    def test_missing_model_file_fails_configuration(self) -> None:
        original = json.loads(Path("configs/admission-baseline.json").read_text())
        original["model"]["path"] = "models/not-present.gguf"
        with tempfile.TemporaryDirectory(dir=".") as folder:
            root = Path(folder)
            (root / "configs").mkdir()
            path = root / "configs" / "admission.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_admission_config(path)

    def test_runtime_factory_rejects_profile_model_mismatch(self) -> None:
        payload = json.loads(Path("configs/admission-baseline.json").read_text())
        payload["model"]["id"] = "wrong/model"
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            dir="configs",
            encoding="utf-8",
            delete=False,
        ) as stream:
            json.dump(payload, stream)
            path = Path(stream.name)
        try:
            with self.assertRaises(ConfigurationError) as caught:
                build_stage7_runtime(admission_config_path=path)
            self.assertEqual(caught.exception.details["mismatched_fields"], ["model_id"])
        finally:
            path.unlink(missing_ok=True)


class AdmissionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_admission_config()
        self.estimator = ConservativeMemoryEstimator(self.config.estimator)
        self.policy = AdmissionPolicy(self.estimator)

    def test_controlled_scenarios_cover_every_required_action(self) -> None:
        outcomes = controlled_decisions(self.config, self.policy)
        self.assertEqual(
            {item["action"] for item in outcomes.values()},
            {action.value for action in AdmissionAction},
        )
        for expected, actual in outcomes.items():
            self.assertEqual(actual["action"], expected.lower())

    def test_unknown_ram_rejects_instead_of_guessing(self) -> None:
        request = AdmissionRequest(self.config.model, 2048, 28)
        snapshot = replace(
            hardware(),
            ram=RamSnapshot(None, None, None, "unavailable", Confidence.UNAVAILABLE),
        )
        decision = self.policy.evaluate(request, snapshot)
        self.assertEqual(decision.action, AdmissionAction.REJECT_UNSAFE)
        self.assertEqual(decision.confidence, Confidence.UNAVAILABLE)


class HardwareCliTests(unittest.TestCase):
    def test_cli_emits_live_and_controlled_inspectable_report(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = hardware_main([])
        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["stage"], 7)
        self.assertIn("profile_ms", payload["hardware"])
        self.assertEqual(
            set(payload["controlled_policy_demonstration"]),
            {action.name for action in AdmissionAction},
        )


class StaticGate:
    def __init__(self, decision):
        self.decision = decision

    def evaluate(self, task, scheduling):
        return self.decision


class RuntimeAdmissionIntegrationTests(unittest.TestCase):
    def _runtime(self, action: AdmissionAction) -> AgentRuntime:
        config = load_admission_config()
        policy = AdmissionPolicy(ConservativeMemoryEstimator(config.estimator))
        decision = policy.evaluate(
            AdmissionRequest(config.model, 2048, 28), hardware()
        )
        if action is not AdmissionAction.ACCEPT:
            decision = replace(
                decision,
                action=action,
                reason="controlled non-accept decision",
            )
        base = build_stage1_runtime()
        runtime = AgentRuntime(
            config=base.config,
            components=replace(base.components, admission=StaticGate(decision)),
        )
        runtime.register_agent(TECHNICAL_EXPLAINER)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        return runtime

    def test_accept_reaches_scheduler_and_is_attached_to_result(self) -> None:
        runtime = self._runtime(AdmissionAction.ACCEPT)
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(result.metadata["admission"]["action"], "accept")
        self.assertEqual(runtime.components.inference.call_count, 1)  # type: ignore[attr-defined]
        names = [event.name for event in runtime.components.events.snapshot(result.task_id)]
        self.assertLess(names.index("admission.evaluated"), names.index("scheduler.request.requested"))

    def test_non_accept_never_reaches_scheduler_or_inference(self) -> None:
        runtime = self._runtime(AdmissionAction.REDUCE_CONTEXT)
        with self.assertRaises(AdmissionControlError) as caught:
            runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(caught.exception.details["decision"]["action"], "reduce_context")
        self.assertEqual(runtime.components.inference.call_count, 0)  # type: ignore[attr-defined]
        created = next(e for e in runtime.components.events.snapshot() if e.name == "task.created")
        self.assertEqual(runtime.task_state(created.task_id), TaskState.RESOURCE_BLOCKED)  # type: ignore[arg-type]
        self.assertEqual(runtime.components.scheduler.snapshot().submitted, 0)


if __name__ == "__main__":
    unittest.main()
