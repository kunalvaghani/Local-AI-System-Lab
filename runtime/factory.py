"""Composition roots for deterministic and real local agent runtimes."""

from dataclasses import replace
from pathlib import Path

from .agents import stage3_agents
from .config import RuntimeConfig
from .errors import ConfigurationError
from .engine import AgentRuntime, RuntimeComponents
from .in_memory import (
    IdentityPolicyEngine,
    InMemoryAgentRegistry,
    InMemoryCheckpointStore,
    InMemoryLifecycleEventStore,
    InMemoryMetricsCollector,
    InlineScheduler,
    StaticModelRouter,
    StubInferenceBackend,
)
from .inference import LlamaCppCompletionBackend, load_llama_cpp_config
from .state_machine import ExecutionStateMachine
from .tools import (
    DefaultDenyToolPolicy,
    ThreadedToolExecutor,
    build_safe_tool_registry,
)
from .scheduler import QueuedScheduler, SchedulerPolicy
from .hardware import LocalHardwareProfiler, MemoryAwareAdmissionGate, load_admission_config
from .adaptive import AdaptiveInferenceController, load_inference_profile_catalog
from .routing import WorkloadModelRouter, load_model_registry
from .persistence import (
    PersistenceConfig,
    SQLiteAgentRegistry,
    SQLiteCheckpointStore,
    SQLiteLifecycleEventStore,
    SQLiteMetricsCollector,
    SQLiteRuntimeStore,
    SQLiteTaskStateMachine,
    load_persistence_config,
)
from .tracing import SQLiteTraceStore


def build_stage1_runtime(config: RuntimeConfig | None = None) -> AgentRuntime:
    """Build the deterministic no-model runtime used by the demo and tests."""

    resolved = config or RuntimeConfig()
    tool_registry = build_safe_tool_registry(Path.cwd())
    components = RuntimeComponents(
        agents=InMemoryAgentRegistry(),
        inference=StubInferenceBackend(
            response_prefix=resolved.stub_response_prefix,
        ),
        scheduler=InlineScheduler(),
        router=StaticModelRouter(model_id=resolved.default_model),
        policy=IdentityPolicyEngine(),
        checkpoints=InMemoryCheckpointStore(),
        metrics=InMemoryMetricsCollector(),
        events=InMemoryLifecycleEventStore(),
        state_machine=ExecutionStateMachine(),
        tool_registry=tool_registry,
        tool_executor=ThreadedToolExecutor(),
        tool_policy=DefaultDenyToolPolicy(),
    )
    return AgentRuntime(config=resolved, components=components)


def build_stage4_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
) -> AgentRuntime:
    """Compose registered agents, explicit state machine, and real backend."""

    inference_config = load_llama_cpp_config(inference_config_path)
    registry = InMemoryAgentRegistry()
    for agent in stage3_agents():
        registry.register(agent)
    tool_registry = build_safe_tool_registry(Path.cwd())
    components = RuntimeComponents(
        agents=registry,
        inference=LlamaCppCompletionBackend(inference_config),
        scheduler=InlineScheduler(),
        router=StaticModelRouter(model_id=inference_config.model_id),
        policy=IdentityPolicyEngine(),
        checkpoints=InMemoryCheckpointStore(),
        metrics=InMemoryMetricsCollector(),
        events=InMemoryLifecycleEventStore(),
        state_machine=ExecutionStateMachine(),
        tool_registry=tool_registry,
        tool_executor=ThreadedToolExecutor(),
        tool_policy=DefaultDenyToolPolicy(),
    )
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-4",
            default_model=inference_config.model_id,
            max_generated_tokens=inference_config.max_generated_tokens,
        ),
        components=components,
    )


def build_stage3_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
) -> AgentRuntime:
    """Compatibility alias; the current runtime includes the Stage 4 machine."""

    return build_stage4_runtime(inference_config_path)


def build_stage5_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
) -> AgentRuntime:
    """Current real runtime with the Stage 5 safe tool subsystem enabled."""

    runtime = build_stage4_runtime(inference_config_path)
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-5",
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
        ),
        components=runtime.components,
    )


def build_stage6_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
) -> AgentRuntime:
    """Current real runtime with one bounded priority scheduler worker."""

    runtime = build_stage5_runtime(inference_config_path)
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-6",
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
        ),
        components=replace(
            runtime.components,
            scheduler=QueuedScheduler(
                policy=SchedulerPolicy.PRIORITY,
                max_workers=1,
            ),
        ),
    )


def build_stage7_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
    admission_config_path: str | Path = "configs/admission-baseline.json",
) -> AgentRuntime:
    """Current real runtime with live, pre-scheduler memory admission."""

    inference_config = load_llama_cpp_config(inference_config_path)
    admission_config = load_admission_config(admission_config_path)
    expected_gpu_layers = (
        admission_config.model.layer_count
        if inference_config.gpu_layers == "all"
        else inference_config.gpu_layers
    )
    mismatches: list[str] = []
    if inference_config.model_id != admission_config.model.model_id:
        mismatches.append("model_id")
    if inference_config.model_path != Path(admission_config.model.path):
        mismatches.append("model_path")
    if inference_config.context_size != admission_config.model.baseline_context_tokens:
        mismatches.append("context_tokens")
    if expected_gpu_layers != admission_config.model.baseline_gpu_layers:
        mismatches.append("gpu_layers")
    if mismatches:
        raise ConfigurationError(
            "admission profile does not match the active inference configuration",
            details={"mismatched_fields": mismatches},
        )
    runtime = build_stage6_runtime(inference_config_path)
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-7",
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
        ),
        components=replace(
            runtime.components,
            admission=MemoryAwareAdmissionGate(
                admission_config
            ),
        ),
    )


def build_stage8_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
    admission_config_path: str | Path = "configs/admission-baseline.json",
    profile_config_path: str | Path = "configs/inference-profiles.json",
) -> AgentRuntime:
    """Current runtime with adaptive, re-admitted llama.cpp resource profiles."""

    runtime = build_stage7_runtime(inference_config_path, admission_config_path)
    admission_config = load_admission_config(admission_config_path)
    catalog = load_inference_profile_catalog(profile_config_path)
    if catalog.model_id != admission_config.model.model_id:
        raise ConfigurationError(
            "inference profile catalog model does not match admission metadata"
        )
    if catalog.layer_count != admission_config.model.layer_count:
        raise ConfigurationError(
            "inference profile catalog layer count does not match admission metadata"
        )
    performance = catalog.get("performance")
    inference_config = load_llama_cpp_config(inference_config_path)
    baseline_gpu_layers = (
        admission_config.model.layer_count
        if inference_config.gpu_layers == "all"
        else inference_config.gpu_layers
    )
    baseline_mismatches = []
    if performance.context_size != inference_config.context_size:
        baseline_mismatches.append("context_size")
    if performance.batch_size != inference_config.batch_size:
        baseline_mismatches.append("batch_size")
    if performance.threads != inference_config.threads:
        baseline_mismatches.append("threads")
    if performance.gpu_layers != baseline_gpu_layers:
        baseline_mismatches.append("gpu_layers")
    if performance.flash_attention != inference_config.flash_attention:
        baseline_mismatches.append("flash_attention")
    if baseline_mismatches:
        raise ConfigurationError(
            "performance profile does not preserve the measured inference baseline",
            details={"mismatched_fields": baseline_mismatches},
        )
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-8",
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
        ),
        components=replace(
            runtime.components,
            admission=None,
            inference_controller=AdaptiveInferenceController(
                catalog,
                admission_config,
            ),
        ),
    )


def build_stage9_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
    admission_config_path: str | Path = "configs/admission-baseline.json",
    profile_config_path: str | Path = "configs/inference-profiles.json",
    registry_config_path: str | Path = "configs/model-registry.json",
) -> AgentRuntime:
    """Compose explainable model routing and task-scoped compute budgets."""

    runtime = build_stage8_runtime(
        inference_config_path,
        admission_config_path,
        profile_config_path,
    )
    registry, budget_policy = load_model_registry(registry_config_path)
    active_model = runtime.config.default_model
    registered = registry.get(active_model)
    if not registered.available:
        raise ConfigurationError(
            "the active inference model is not available in the Stage 9 registry",
            details={"model_id": active_model},
        )
    configured_models = [
        model.model_id for model in registry.models if model.backend_configured
    ]
    if configured_models != [active_model]:
        raise ConfigurationError(
            "Stage 9 single-backend composition must configure only the active model",
            details={"configured_models": configured_models, "active_model": active_model},
        )
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name="local-ai-systems-lab-stage-9",
            default_model=active_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
        ),
        components=replace(
            runtime.components,
            router=WorkloadModelRouter(registry),
            budget_policy=budget_policy,
            hardware_profiler=LocalHardwareProfiler(),
        ),
    )


def _with_stage10_persistence(
    runtime: AgentRuntime,
    persistence_config: PersistenceConfig,
    *,
    runtime_name: str,
) -> AgentRuntime:
    store = SQLiteRuntimeStore(persistence_config)
    for agent in runtime.components.agents.snapshot():
        store.ensure_agent(agent)
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name=runtime_name,
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
            stub_response_prefix=runtime.config.stub_response_prefix,
        ),
        components=replace(
            runtime.components,
            agents=SQLiteAgentRegistry(store),
            checkpoints=SQLiteCheckpointStore(store),
            metrics=SQLiteMetricsCollector(store),
            events=SQLiteLifecycleEventStore(store),
            state_machine=SQLiteTaskStateMachine(store),
            persistence=store,
        ),
    )


def build_stage10_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
    admission_config_path: str | Path = "configs/admission-baseline.json",
    profile_config_path: str | Path = "configs/inference-profiles.json",
    registry_config_path: str | Path = "configs/model-registry.json",
    persistence_config_path: str | Path = "configs/persistence.json",
    database_path: str | Path | None = None,
) -> AgentRuntime:
    """Compose the real Stage 9 runtime with durable SQLite state."""

    runtime = build_stage9_runtime(
        inference_config_path,
        admission_config_path,
        profile_config_path,
        registry_config_path,
    )
    persistence_config = load_persistence_config(persistence_config_path)
    if database_path is not None:
        persistence_config = replace(
            persistence_config,
            database_path=Path(database_path).resolve(),
        )
    return _with_stage10_persistence(
        runtime,
        persistence_config,
        runtime_name="local-ai-systems-lab-stage-10",
    )


def build_stage10_stub_runtime(
    database_path: str | Path,
    persistence_config_path: str | Path = "configs/persistence.json",
) -> AgentRuntime:
    """Deterministic Stage 10 composition for restart/recovery tests and demos."""

    persistence_config = replace(
        load_persistence_config(persistence_config_path),
        database_path=Path(database_path).resolve(),
    )
    runtime = build_stage1_runtime(
        RuntimeConfig(runtime_name="local-ai-systems-lab-stage-10-stub")
    )
    for agent in stage3_agents():
        runtime.register_agent(agent)
    return _with_stage10_persistence(
        runtime,
        persistence_config,
        runtime_name="local-ai-systems-lab-stage-10-stub",
    )


def _with_stage11_tracing(runtime: AgentRuntime, *, runtime_name: str) -> AgentRuntime:
    store = runtime.components.persistence
    if not isinstance(store, SQLiteRuntimeStore):
        raise ConfigurationError("Stage 11 tracing requires SQLite runtime persistence")
    return AgentRuntime(
        config=RuntimeConfig(
            runtime_name=runtime_name,
            default_model=runtime.config.default_model,
            max_generated_tokens=runtime.config.max_generated_tokens,
            stub_response_prefix=runtime.config.stub_response_prefix,
        ),
        components=replace(
            runtime.components,
            traces=SQLiteTraceStore(store),
        ),
    )


def build_stage11_runtime(
    inference_config_path: str | Path = "configs/inference-baseline.json",
    admission_config_path: str | Path = "configs/admission-baseline.json",
    profile_config_path: str | Path = "configs/inference-profiles.json",
    registry_config_path: str | Path = "configs/model-registry.json",
    persistence_config_path: str | Path = "configs/persistence.json",
    database_path: str | Path | None = None,
) -> AgentRuntime:
    """Compose durable execution with structured traces and replay access."""

    runtime = build_stage10_runtime(
        inference_config_path,
        admission_config_path,
        profile_config_path,
        registry_config_path,
        persistence_config_path,
        database_path,
    )
    return _with_stage11_tracing(
        runtime,
        runtime_name="local-ai-systems-lab-stage-11",
    )


def build_stage11_stub_runtime(
    database_path: str | Path,
    persistence_config_path: str | Path = "configs/persistence.json",
) -> AgentRuntime:
    """Deterministic Stage 11 composition for replay and comparison evidence."""

    runtime = build_stage10_stub_runtime(database_path, persistence_config_path)
    return _with_stage11_tracing(
        runtime,
        runtime_name="local-ai-systems-lab-stage-11-stub",
    )
