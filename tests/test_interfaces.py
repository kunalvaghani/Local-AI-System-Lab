import unittest

from runtime.factory import build_stage1_runtime
from runtime.interfaces import (
    CheckpointStore,
    InferenceBackend,
    MetricsCollector,
    ModelRouter,
    PolicyEngine,
    Scheduler,
)


class InterfaceCompositionTests(unittest.TestCase):
    def test_factory_components_satisfy_runtime_protocols(self) -> None:
        components = build_stage1_runtime().components

        self.assertIsInstance(components.inference, InferenceBackend)
        self.assertIsInstance(components.scheduler, Scheduler)
        self.assertIsInstance(components.router, ModelRouter)
        self.assertIsInstance(components.policy, PolicyEngine)
        self.assertIsInstance(components.checkpoints, CheckpointStore)
        self.assertIsInstance(components.metrics, MetricsCollector)


if __name__ == "__main__":
    unittest.main()
