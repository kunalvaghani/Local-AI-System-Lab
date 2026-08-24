import unittest

from runtime.factory import build_stage1_runtime, build_stage7_runtime, build_stage8_runtime
from runtime.interfaces import (
    AdmissionGate,
    AgentRegistry,
    CheckpointStore,
    InferenceBackend,
    InferenceController,
    LifecycleEventStore,
    MetricsCollector,
    ModelRouter,
    PolicyEngine,
    Scheduler,
    TaskStateMachine,
    ToolExecutor,
    ToolPolicy,
    ToolRegistry,
)


class InterfaceCompositionTests(unittest.TestCase):
    def test_factory_components_satisfy_runtime_protocols(self) -> None:
        components = build_stage1_runtime().components

        self.assertIsInstance(components.agents, AgentRegistry)
        self.assertIsInstance(components.inference, InferenceBackend)
        self.assertIsInstance(components.scheduler, Scheduler)
        self.assertIsInstance(components.router, ModelRouter)
        self.assertIsInstance(components.policy, PolicyEngine)
        self.assertIsInstance(components.checkpoints, CheckpointStore)
        self.assertIsInstance(components.metrics, MetricsCollector)
        self.assertIsInstance(components.events, LifecycleEventStore)
        self.assertIsInstance(components.state_machine, TaskStateMachine)
        self.assertIsInstance(components.tool_registry, ToolRegistry)
        self.assertIsInstance(components.tool_executor, ToolExecutor)
        self.assertIsInstance(components.tool_policy, ToolPolicy)

        stage7 = build_stage7_runtime().components
        self.assertIsInstance(stage7.admission, AdmissionGate)

        stage8 = build_stage8_runtime().components
        self.assertIsInstance(stage8.inference_controller, InferenceController)


if __name__ == "__main__":
    unittest.main()
