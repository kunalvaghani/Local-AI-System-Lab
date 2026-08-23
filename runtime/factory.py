"""Composition root for the Stage 1 runnable skeleton."""

from .config import RuntimeConfig
from .engine import AgentRuntime, RuntimeComponents
from .in_memory import (
    IdentityPolicyEngine,
    InMemoryCheckpointStore,
    InMemoryMetricsCollector,
    InlineScheduler,
    StaticModelRouter,
    StubInferenceBackend,
)


def build_stage1_runtime(config: RuntimeConfig | None = None) -> AgentRuntime:
    """Build the deterministic no-model runtime used by the demo and tests."""

    resolved = config or RuntimeConfig()
    components = RuntimeComponents(
        inference=StubInferenceBackend(
            response_prefix=resolved.stub_response_prefix,
        ),
        scheduler=InlineScheduler(),
        router=StaticModelRouter(model_id=resolved.default_model),
        policy=IdentityPolicyEngine(),
        checkpoints=InMemoryCheckpointStore(),
        metrics=InMemoryMetricsCollector(),
    )
    return AgentRuntime(config=resolved, components=components)
