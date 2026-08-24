import json
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path

from runtime.agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from runtime.adaptive import AdaptiveInferenceController, load_inference_profile_catalog
from runtime.engine import AgentRuntime
from runtime.errors import ComputeBudgetExceededError, ConfigurationError, ModelRoutingError
from runtime.factory import build_stage1_runtime, build_stage9_runtime
from runtime.hardware import Confidence, CpuSnapshot, GpuSnapshot, HardwareSnapshot, RamSnapshot
from runtime.hardware import load_admission_config
from runtime.models import Task, TaskState
from runtime.routing import ComputeBudget, RoutingContext, WorkloadModelRouter, load_model_registry
from runtime.routing_cli import main as routing_main
from runtime.scheduler import SchedulingOptions, WorkloadClass


def hardware() -> HardwareSnapshot:
    return HardwareSnapshot(
        CpuSnapshot("CPU", 16, 8, "test", Confidence.HIGH),
        RamSnapshot(32000.0, 16000.0, 16000.0, "test", Confidence.HIGH),
        GpuSnapshot("GPU", "driver", 4096.0, 100.0, 3996.0, 0.0, 50.0, "8.6", "test", Confidence.HIGH),
    )


class FixedProfiler:
    def snapshot(self) -> HardwareSnapshot:
        return hardware()


def controlled_registry():
    registry, policy = load_model_registry()
    path = registry.available_models[0].path
    registry = replace(
        registry,
        models=tuple(replace(model, path=path, backend_configured=True) for model in registry.models),
    )
    return registry, policy


class RegistryTests(unittest.TestCase):
    def test_registry_is_typed_and_availability_is_truthful(self) -> None:
        registry, policy = load_model_registry()
        self.assertEqual(len(registry.models), 2)
        self.assertEqual([model.model_id for model in registry.available_models], ["Qwen/Qwen2.5-1.5B-Instruct-GGUF"])
        self.assertIsNotNone(registry.available_models[0].benchmark)
        self.assertEqual(policy.resolve(WorkloadClass.BACKGROUND).max_generated_tokens, 32)

    def test_duplicate_model_ids_fail_configuration(self) -> None:
        payload = json.loads(Path("configs/model-registry.json").read_text(encoding="utf-8"))
        payload["models"].append(dict(payload["models"][0]))
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as stream:
            json.dump(payload, stream)
            path = Path(stream.name)
        try:
            with self.assertRaises(ConfigurationError):
                load_model_registry(path)
        finally:
            path.unlink(missing_ok=True)


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry, self.policy = controlled_registry()
        self.router = WorkloadModelRouter(self.registry)

    def context(self, workload: WorkloadClass) -> RoutingContext:
        return RoutingContext(SchedulingOptions(workload=workload), self.policy.resolve(workload), 0, hardware())

    def test_workload_categories_automatically_route_differently(self) -> None:
        interactive = self.router.route(
            Task.create(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="Explain local inference briefly"),
            TECHNICAL_EXPLAINER,
            self.context(WorkloadClass.INTERACTIVE),
        )
        risk = self.router.route(
            Task.create(agent_id=RISK_ANALYST.agent_id, objective="Analyze GPU memory risk"),
            RISK_ANALYST,
            self.context(WorkloadClass.STANDARD),
        )
        self.assertEqual(interactive.model_id, "Qwen/Qwen2.5-0.5B-Instruct-GGUF")
        self.assertEqual(risk.model_id, "Qwen/Qwen2.5-1.5B-Instruct-GGUF")
        self.assertIn("highest among safe available candidates", interactive.reason)
        rejected = next(item for item in risk.evidence["candidates"] if item["model_id"].endswith("0.5B-Instruct-GGUF"))
        self.assertFalse(rejected["accepted"])
        self.assertIn("capability risk_analysis is not declared", rejected["reasons"])

    def test_context_over_limit_explains_every_rejection(self) -> None:
        task = Task.create(agent_id=TECHNICAL_EXPLAINER.agent_id, objective="Explain", input_data={"context_length": 4096})
        with self.assertRaises(ModelRoutingError) as caught:
            self.router.route(task, TECHNICAL_EXPLAINER, self.context(WorkloadClass.INTERACTIVE))
        self.assertTrue(all(any("context 4096 exceeds" in reason for reason in item["reasons"]) for item in caught.exception.details["candidates"]))


class BudgetRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        registry, policy = controlled_registry()
        base = build_stage1_runtime()
        self.runtime = AgentRuntime(
            config=base.config,
            components=replace(
                base.components,
                router=WorkloadModelRouter(registry),
                budget_policy=policy,
                hardware_profiler=FixedProfiler(),
            ),
        )
        self.runtime.register_agent(TECHNICAL_EXPLAINER)
        self.runtime.start()
        self.addCleanup(self.runtime.shutdown)

    def test_token_and_time_budgets_reach_execution_boundary(self) -> None:
        result = self.runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE, timeout_ms=20000),
            compute_budget=ComputeBudget(1, 7, 5000, 2048.0, 1536.0),
        )
        self.assertEqual(self.runtime.components.inference.last_request.max_generated_tokens, 7)  # type: ignore[attr-defined,union-attr]
        self.assertLessEqual(result.metadata["scheduler"]["timeout_ms"], 5000)
        self.assertEqual(result.metadata["compute_budget"]["max_generated_tokens"], 7)
        names = [event.name for event in self.runtime.components.events.snapshot(result.task_id)]
        self.assertLess(names.index("compute_budget.evaluated"), names.index("scheduler.request.requested"))

    def test_zero_call_budget_blocks_before_scheduler_and_backend(self) -> None:
        with self.assertRaises(ComputeBudgetExceededError):
            self.runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE),
                compute_budget=ComputeBudget(0, 7, 5000, 2048.0, 1536.0),
            )
        self.assertEqual(self.runtime.components.inference.call_count, 0)  # type: ignore[attr-defined]
        self.assertEqual(self.runtime.components.scheduler.snapshot().submitted, 0)
        created = next(event for event in self.runtime.components.events.snapshot() if event.name == "task.created")
        self.assertEqual(self.runtime.task_state(created.task_id), TaskState.RESOURCE_BLOCKED)  # type: ignore[arg-type]

    def test_vram_budget_selects_a_smaller_exact_profile(self) -> None:
        controller = AdaptiveInferenceController(
            load_inference_profile_catalog(),
            load_admission_config(),
            FixedProfiler(),  # type: ignore[arg-type]
        )
        runtime = AgentRuntime(
            config=self.runtime.config,
            components=replace(
                self.runtime.components,
                inference_controller=controller,
            ),
        )
        self.runtime.shutdown()
        runtime.start()
        self.addCleanup(runtime.shutdown)
        result = runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE),
            compute_budget=ComputeBudget(1, 16, 5000, 2048.0, 600.0),
        )
        self.assertEqual(
            result.metadata["profile_selection"]["selected_profile"]["profile_id"],
            "constrained",
        )
        attempts = result.metadata["profile_selection"]["attempts"]
        self.assertIn("predicted VRAM exceeds max_vram_mib", attempts[0]["budget_constraints"])


class Stage9CompositionTests(unittest.TestCase):
    def test_factory_composes_registry_router_budget_and_profiler(self) -> None:
        runtime = build_stage9_runtime()
        self.assertIsInstance(runtime.components.router, WorkloadModelRouter)
        self.assertIsNotNone(runtime.components.budget_policy)
        self.assertIsNotNone(runtime.components.hardware_profiler)

    def test_cli_exposes_live_controlled_routes_and_budget_block(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            code = routing_main([])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["stage"], 9)
        self.assertNotEqual(
            payload["controlled_two_model_routes"]["interactive_explanation"]["model_id"],
            payload["controlled_two_model_routes"]["standard_risk_analysis"]["model_id"],
        )
        self.assertEqual(payload["budget_demo"]["token_cap_applied"], 7)
        self.assertEqual(payload["budget_demo"]["zero_call_budget"]["code"], "compute_budget_exceeded")


if __name__ == "__main__":
    unittest.main()
