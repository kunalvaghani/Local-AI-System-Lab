"""Retain reproducible Stage 9 routing decisions without invoking a real model."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from runtime.agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from runtime.hardware import LocalHardwareProfiler
from runtime.models import Task
from runtime.routing import RoutingContext, WorkloadModelRouter, load_model_registry
from runtime.scheduler import SchedulingOptions, WorkloadClass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="benchmarks/results")
    args = parser.parse_args()
    registry, policy = load_model_registry()
    hardware = LocalHardwareProfiler().snapshot()
    installed_path = registry.available_models[0].path
    controlled_registry = replace(
        registry,
        models=tuple(
            replace(model, path=installed_path, backend_configured=True)
            for model in registry.models
        ),
    )
    router = WorkloadModelRouter(controlled_registry)
    scenarios = (
        ("interactive_explanation", TECHNICAL_EXPLAINER, WorkloadClass.INTERACTIVE),
        ("standard_risk_analysis", RISK_ANALYST, WorkloadClass.STANDARD),
    )
    decisions = {}
    for name, agent, workload in scenarios:
        task = Task.create(agent_id=agent.agent_id, objective=agent.objective)
        decisions[name] = router.route(
            task,
            agent,
            RoutingContext(
                SchedulingOptions(workload=workload),
                policy.resolve(workload),
                0,
                hardware,
            ),
        ).as_dict()
    captured = datetime.now(timezone.utc)
    payload = {
        "stage": 9,
        "captured_at_utc": captured.isoformat(),
        "mode": "controlled router evaluation; compact model availability is simulated and no compact inference is claimed",
        "live_registry": [model.as_dict() for model in registry.models],
        "decisions": decisions,
        "different_models_selected": len({item["model_id"] for item in decisions.values()}) == len(decisions),
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"stage9-routing-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(path), "selections": {name: item["model_id"] for name, item in decisions.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
