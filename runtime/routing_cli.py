"""Stage 9 registry, routing, and compute-budget demonstration."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Sequence

from .agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from .errors import LabError
from .factory import build_stage1_runtime
from .hardware import LocalHardwareProfiler
from .models import Task
from .routing import ComputeBudget, RoutingContext, WorkloadModelRouter, load_model_registry
from .scheduler import SchedulingOptions, WorkloadClass


class FixedProfiler:
    def __init__(self, snapshot: Any) -> None:
        self._snapshot = snapshot

    def snapshot(self) -> Any:
        return self._snapshot


def _decision(router: WorkloadModelRouter, task: Task, agent: Any, workload: WorkloadClass, budget: ComputeBudget, hardware: Any) -> dict[str, Any]:
    return router.route(
        task,
        agent,
        RoutingContext(SchedulingOptions(workload=workload), budget, 0, hardware),
    ).as_dict()


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    registry, policy = load_model_registry()
    hardware = LocalHardwareProfiler().snapshot()
    live_router = WorkloadModelRouter(registry)
    live_interactive = _decision(
        live_router,
        Task.create(agent_id=TECHNICAL_EXPLAINER.agent_id, objective=TECHNICAL_EXPLAINER.objective),
        TECHNICAL_EXPLAINER,
        WorkloadClass.INTERACTIVE,
        policy.resolve(WorkloadClass.INTERACTIVE),
        hardware,
    )
    live_risk = _decision(
        live_router,
        Task.create(agent_id=RISK_ANALYST.agent_id, objective=RISK_ANALYST.objective),
        RISK_ANALYST,
        WorkloadClass.STANDARD,
        policy.resolve(WorkloadClass.STANDARD),
        hardware,
    )

    installed_path = registry.available_models[0].path
    controlled_registry = replace(
        registry,
        models=tuple(
            replace(model, path=installed_path, backend_configured=True)
            for model in registry.models
        ),
    )
    controlled_router = WorkloadModelRouter(controlled_registry)
    controlled = {
        "interactive_explanation": _decision(
            controlled_router,
            Task.create(agent_id=TECHNICAL_EXPLAINER.agent_id, objective=TECHNICAL_EXPLAINER.objective),
            TECHNICAL_EXPLAINER,
            WorkloadClass.INTERACTIVE,
            policy.resolve(WorkloadClass.INTERACTIVE),
            hardware,
        ),
        "standard_risk_analysis": _decision(
            controlled_router,
            Task.create(agent_id=RISK_ANALYST.agent_id, objective=RISK_ANALYST.objective),
            RISK_ANALYST,
            WorkloadClass.STANDARD,
            policy.resolve(WorkloadClass.STANDARD),
            hardware,
        ),
    }

    base = build_stage1_runtime()
    runtime = type(base)(
        config=base.config,
        components=replace(
            base.components,
            router=controlled_router,
            budget_policy=policy,
            hardware_profiler=FixedProfiler(hardware),
        ),
    )
    runtime.register_agent(TECHNICAL_EXPLAINER)
    runtime.start()
    try:
        capped = runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE),
            compute_budget=ComputeBudget(1, 7, 5000, 2048.0, 1536.0),
        )
        blocked: dict[str, Any]
        try:
            runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE),
                compute_budget=ComputeBudget(0, 7, 5000, 2048.0, 1536.0),
            )
            blocked = {"unexpected": "execution was not blocked"}
        except LabError as error:
            blocked = error.as_dict()
    finally:
        runtime.shutdown()

    print(json.dumps({
        "stage": 9,
        "purpose": "select an explainable local model route and enforce task-scoped compute limits",
        "registry": [model.as_dict() for model in registry.models],
        "live_routes": {"interactive_explanation": live_interactive, "standard_risk_analysis": live_risk},
        "controlled_two_model_routes": controlled,
        "controlled_boundary": "The compact candidate is marked available only for router evaluation and deterministic stub execution; no compact GGUF inference or benchmark is claimed.",
        "budget_demo": {
            "token_cap_requested": 7,
            "token_cap_applied": base.components.inference.last_request.max_generated_tokens,
            "accepted_usage": capped.metadata["compute_usage"],
            "zero_call_budget": blocked,
        },
        "component_roles": {
            "model_registry": "tracks local artifacts, capabilities, limits, availability, and measured benchmark provenance",
            "workload_router": "scores safe candidates from task, workload, latency, queue, hardware, and budget evidence",
            "compute_budget_policy": "sets workload defaults and accepts explicit task overrides",
            "runtime_budget_gate": "caps calls, tokens, time, and estimated memory before scheduler submission",
            "adaptive_controller": "re-admits the exact selected inference profile after routing",
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
