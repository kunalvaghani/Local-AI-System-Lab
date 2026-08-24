import json
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path

from runtime.adaptive import (
    AdaptiveInferenceController,
    load_inference_profile_catalog,
)
from runtime.adaptive_cli import main as adaptive_main
from runtime.agents import TECHNICAL_EXPLAINER
from runtime.engine import AgentRuntime
from runtime.errors import AdmissionControlError, ConfigurationError, ValidationError
from runtime.factory import build_stage1_runtime, build_stage8_runtime
from runtime.hardware import (
    Confidence,
    CpuSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    RamSnapshot,
    load_admission_config,
)
from runtime.inference.llama_cpp import LlamaCppCompletionBackend
from runtime.models import InferenceProfile, InferenceRequest, Task, TaskState, utc_now
from runtime.scheduler import SchedulingOptions, WorkloadClass
from tests.test_llama_cpp_backend import fake_config


def snapshot(
    *,
    free_vram_mib: float = 3962.0,
    gpu_present: bool = True,
    available_ram_mib: float | None = 16000.0,
) -> HardwareSnapshot:
    ram = (
        RamSnapshot(32000.0, available_ram_mib, 32000.0 - available_ram_mib, "test", Confidence.HIGH)
        if available_ram_mib is not None
        else RamSnapshot(None, None, None, "unavailable", Confidence.UNAVAILABLE)
    )
    gpu = (
        GpuSnapshot(
            "GPU",
            "driver",
            4096.0,
            4096.0 - free_vram_mib,
            free_vram_mib,
            0.0,
            50.0,
            "8.6",
            "test",
            Confidence.HIGH,
        )
        if gpu_present
        else None
    )
    return HardwareSnapshot(
        CpuSnapshot("CPU", 16, 8, "test", Confidence.HIGH),
        ram,
        gpu,
    )


class FixedProfiler:
    def __init__(self, value: HardwareSnapshot) -> None:
        self.value = value
        self.calls = 0

    def snapshot(self) -> HardwareSnapshot:
        self.calls += 1
        return self.value


class ProfileCatalogTests(unittest.TestCase):
    def test_catalog_is_typed_complete_and_baseline_is_preserved(self) -> None:
        catalog = load_inference_profile_catalog()
        self.assertEqual(len(catalog.profiles), 4)
        self.assertEqual(catalog.get("performance").gpu_layers, 28)
        self.assertEqual(catalog.get("performance").context_size, 2048)
        self.assertEqual(catalog.get("cpu_safe").gpu_layers, 0)
        self.assertEqual(catalog.get("cpu_safe").devices, "none")
        for order in catalog.workload_order.values():
            self.assertEqual(set(order), {profile.profile_id for profile in catalog.profiles})

    def test_invalid_profile_values_fail_before_execution(self) -> None:
        with self.assertRaises(ValidationError):
            InferenceProfile("bad", "bad", 1024, 64, 128, 8, 8, 0, "off")

    def test_catalog_rejects_incomplete_workload_order(self) -> None:
        payload = json.loads(Path("configs/inference-profiles.json").read_text())
        payload["workload_order"]["standard"].pop()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as stream:
            json.dump(payload, stream)
            path = Path(stream.name)
        try:
            with self.assertRaises(ConfigurationError):
                load_inference_profile_catalog(path)
        finally:
            path.unlink(missing_ok=True)


class AdaptiveControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_inference_profile_catalog()
        self.admission = load_admission_config()
        self.task = Task("task", "agent", "objective", utc_now())

    def _controller(self, hardware: HardwareSnapshot):
        profiler = FixedProfiler(hardware)
        return AdaptiveInferenceController(
            self.catalog,
            self.admission,
            profiler,  # type: ignore[arg-type]
        ), profiler

    def test_ample_memory_selects_workload_preference_from_one_snapshot(self) -> None:
        controller, profiler = self._controller(snapshot())
        interactive = controller.select(
            self.task, SchedulingOptions(workload=WorkloadClass.INTERACTIVE)
        )
        self.assertEqual(interactive.selected_profile.profile_id, "performance")  # type: ignore[union-attr]
        self.assertEqual(len(interactive.attempts), 1)
        self.assertEqual(profiler.calls, 1)

        controller, _ = self._controller(snapshot())
        background = controller.select(
            self.task, SchedulingOptions(workload=WorkloadClass.BACKGROUND)
        )
        self.assertEqual(background.selected_profile.profile_id, "balanced")  # type: ignore[union-attr]

    def test_gpu_pressure_falls_to_first_profile_that_is_re_admitted(self) -> None:
        controller, _ = self._controller(snapshot(free_vram_mib=1500.0))
        selection = controller.select(self.task, SchedulingOptions())
        self.assertEqual(selection.selected_profile.profile_id, "balanced")  # type: ignore[union-attr]
        self.assertEqual(
            [attempt.admission.action.value for attempt in selection.attempts],
            ["queue", "accept"],
        )

    def test_missing_gpu_selects_zero_offload_profile(self) -> None:
        controller, _ = self._controller(snapshot(gpu_present=False))
        selection = controller.select(self.task, SchedulingOptions())
        self.assertEqual(selection.selected_profile.profile_id, "cpu_safe")  # type: ignore[union-attr]
        self.assertEqual(selection.selected_profile.gpu_layers, 0)  # type: ignore[union-attr]

    def test_unknown_ram_admits_no_profile(self) -> None:
        controller, _ = self._controller(snapshot(available_ram_mib=None))
        selection = controller.select(self.task, SchedulingOptions())
        self.assertFalse(selection.permitted)
        self.assertIsNone(selection.selected_profile)
        self.assertEqual(len(selection.attempts), 4)


class BackendProfileTests(unittest.TestCase):
    def test_selected_profile_changes_every_supported_native_flag(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / "fake.gguf"
            model.write_bytes(b"model")
            backend = LlamaCppCompletionBackend(fake_config(model))
            profile = load_inference_profile_catalog().get("balanced")
            request = InferenceRequest("task", "prompt", "test/fake-gguf", 16, profile=profile)
            command = backend._build_command(request)
            expected = {
                "--ctx-size": "1536",
                "--batch-size": "192",
                "--ubatch-size": "192",
                "--threads": "8",
                "--threads-batch": "8",
                "--gpu-layers": "20",
                "--flash-attn": "on",
                "--device": "CUDA0",
            }
            for flag, value in expected.items():
                self.assertEqual(command[command.index(flag) + 1], value)

    def test_backend_result_reports_the_applied_profile(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / "fake.gguf"
            model.write_bytes(b"model")
            backend = LlamaCppCompletionBackend(fake_config(model))
            backend.start()
            self.addCleanup(backend.shutdown)
            profile = load_inference_profile_catalog().get("constrained")
            request = InferenceRequest("task", "prompt", "test/fake-gguf", 16, profile=profile)
            result = backend.generate(request)
            self.assertEqual(result.metadata["inference_profile"]["profile_id"], "constrained")


class RuntimeControllerIntegrationTests(unittest.TestCase):
    def _runtime(self, hardware: HardwareSnapshot) -> AgentRuntime:
        base = build_stage1_runtime()
        controller = AdaptiveInferenceController(
            load_inference_profile_catalog(),
            load_admission_config(),
            FixedProfiler(hardware),  # type: ignore[arg-type]
        )
        runtime = AgentRuntime(
            config=base.config,
            components=replace(
                base.components,
                admission=None,
                inference_controller=controller,
            ),
        )
        runtime.register_agent(TECHNICAL_EXPLAINER)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        return runtime

    def test_runtime_passes_selected_profile_to_backend_before_scheduler(self) -> None:
        runtime = self._runtime(snapshot(free_vram_mib=1500.0))
        result = runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(result.metadata["profile_selection"]["selected_profile"]["profile_id"], "balanced")
        self.assertEqual(runtime.components.inference.last_request.profile.profile_id, "balanced")  # type: ignore[attr-defined,union-attr]
        names = [event.name for event in runtime.components.events.snapshot(result.task_id)]
        self.assertLess(
            names.index("inference.profile.selection.evaluated"),
            names.index("scheduler.request.requested"),
        )

    def test_no_safe_profile_is_resource_blocked_before_scheduler(self) -> None:
        runtime = self._runtime(snapshot(available_ram_mib=None))
        with self.assertRaises(AdmissionControlError):
            runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        self.assertEqual(runtime.components.inference.call_count, 0)  # type: ignore[attr-defined]
        self.assertEqual(runtime.components.scheduler.snapshot().submitted, 0)
        created = next(e for e in runtime.components.events.snapshot() if e.name == "task.created")
        self.assertEqual(runtime.task_state(created.task_id), TaskState.RESOURCE_BLOCKED)  # type: ignore[arg-type]


class AdaptiveCliTests(unittest.TestCase):
    def test_cli_exposes_live_and_controlled_selection(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = adaptive_main([])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["stage"], 8)
        self.assertEqual(len(payload["profiles"]), 4)
        self.assertEqual(
            payload["controlled_selection"]["gpu_pressure"]["selected_profile"]["profile_id"],
            "balanced",
        )
        self.assertFalse(payload["controlled_selection"]["missing_ram"]["permitted"])
        self.assertEqual(
            payload["controlled_selection"]["missing_gpu"]["selected_profile"]["profile_id"],
            "cpu_safe",
        )

    def test_stage8_factory_composes_controller(self) -> None:
        runtime = build_stage8_runtime()
        self.assertIsNone(runtime.components.admission)
        self.assertIsNotNone(runtime.components.inference_controller)


if __name__ == "__main__":
    unittest.main()
