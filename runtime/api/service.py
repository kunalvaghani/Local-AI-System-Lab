"""Transport-independent Stage 15 API operations over the complete runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..chaos_cli import _run as run_chaos_suite
from ..engine import AgentRuntime
from ..errors import ApiRequestError, ConfigurationError, TaskNotFoundError
from ..routing import load_model_registry
from ..scheduler import WorkloadClass
from ..tracing import TraceReplayEngine
from .config import ApiConfig
from .manager import ApiTaskManager


def _positive_query(value: str | None, name: str) -> int | None:
    if value is None:
        return None
    try:
        resolved = int(value)
    except ValueError as error:
        raise ApiRequestError(f"query parameter {name} must be an integer") from error
    if resolved <= 0:
        raise ApiRequestError(f"query parameter {name} must be positive")
    return resolved


class RuntimeApiService:
    """Stable application service; HTTP is only one adapter around it."""

    def __init__(
        self,
        runtime: AgentRuntime,
        config: ApiConfig,
        *,
        model_registry_path: str | Path = "configs/model-registry.json",
        chaos_config_path: str | Path = "configs/chaos.json",
        chaos_data_directory: str | Path = "data",
    ) -> None:
        self.runtime = runtime
        self.config = config
        self.tasks = ApiTaskManager(runtime, max_inflight_tasks=config.max_inflight_tasks)
        self._model_registry_path = Path(model_registry_path)
        self._chaos_config_path = str(chaos_config_path)
        self._chaos_data_directory = Path(chaos_data_directory).resolve()

    def discovery(self) -> dict[str, Any]:
        return {
            "name": "Local AI Systems Lab API",
            "api_version": "v1",
            "stage": 15,
            "transport": "HTTP/1.1 JSON and Server-Sent Events",
            "scope": "loopback development interface",
            "documentation": "/v1/openapi.json",
            "endpoints": {
                "health": "/v1/health",
                "tasks": "/v1/tasks",
                "agents": "/v1/agents",
                "scheduler": "/v1/scheduler",
                "hardware": "/v1/hardware",
                "models": "/v1/models",
                "metrics": "/v1/metrics",
                "trace": "/v1/traces/{run_id}",
                "chaos": "/v1/chaos",
                "security_results": "/v1/security/results",
            },
        }

    def health(self) -> dict[str, Any]:
        persistence = self.runtime.components.persistence
        return {
            "status": "ok" if self.runtime.status.value == "running" else "unavailable",
            "runtime_status": self.runtime.status.value,
            "runtime_name": self.runtime.config.runtime_name,
            "persistence": {
                "configured": persistence is not None,
                "schema_version": persistence.schema_version if persistence else None,
                "integrity": persistence.integrity_check() if persistence else None,
            },
        }

    def create_task(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {"agent_id", "objective", "input_data", "workload", "timeout_ms"}
        self._exact_fields(payload, allowed, required={"agent_id"})
        agent_id = payload["agent_id"]
        objective = payload.get("objective")
        input_data = payload.get("input_data")
        if not isinstance(agent_id, str) or not agent_id.strip():
            raise ApiRequestError("agent_id must be a non-empty string")
        if objective is not None and (not isinstance(objective, str) or not objective.strip()):
            raise ApiRequestError("objective must be a non-empty string when supplied")
        if input_data is not None and not isinstance(input_data, dict):
            raise ApiRequestError("input_data must be a JSON object when supplied")
        try:
            workload = WorkloadClass(payload.get("workload", WorkloadClass.STANDARD.value))
        except (TypeError, ValueError) as error:
            raise ApiRequestError(
                "workload must be interactive, standard, or background"
            ) from error
        timeout_ms = payload.get("timeout_ms", self.config.default_task_timeout_ms)
        if (
            isinstance(timeout_ms, bool)
            or not isinstance(timeout_ms, int)
            or not 1 <= timeout_ms <= self.config.max_task_timeout_ms
        ):
            raise ApiRequestError(
                "timeout_ms is outside the configured API range",
                details={"maximum": self.config.max_task_timeout_ms},
            )
        record = self.tasks.create(
            agent_id=agent_id,
            objective=objective,
            input_data=input_data,
            workload=workload,
            timeout_ms=timeout_ms,
        )
        return self.tasks.inspect(record.task.task_id)

    def task_trace(self, task_id: str) -> dict[str, Any]:
        self.tasks.inspect(task_id)
        traces = self.runtime.components.traces
        if traces is None:
            raise ConfigurationError("trace store is not configured")
        run = traces.for_task(task_id)
        return self._safe_trace(run, traces.steps(run.run_id))

    def trace(self, run_id: str) -> dict[str, Any]:
        traces = self.runtime.components.traces
        if traces is None:
            raise ConfigurationError("trace store is not configured")
        run = traces.load_run(run_id)
        return self._safe_trace(run, traces.steps(run_id))

    def replay_trace(self, run_id: str) -> dict[str, Any]:
        traces = self.runtime.components.traces
        if traces is None:
            raise ConfigurationError("trace store is not configured")
        return TraceReplayEngine(traces).replay(run_id).as_dict()

    @staticmethod
    def _safe_trace(run: Any, steps: Any) -> dict[str, Any]:
        run_payload = run.as_dict()
        run_payload.pop("metadata", None)
        safe_steps: list[dict[str, Any]] = []
        for step in steps:
            item = step.as_dict(include_payloads=False)
            failure = item.get("failure")
            if isinstance(failure, dict):
                item["failure"] = {
                    "code": failure.get("code", "failure"),
                    "details_omitted": True,
                }
            safe_steps.append(item)
        return {
            "run": run_payload,
            "steps": safe_steps,
            "payload_policy": "input/output payloads and failure details are omitted; integrity hashes are exposed",
        }

    def agents(self) -> dict[str, Any]:
        return {
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "objective": agent.objective,
                    "capabilities": sorted(agent.capabilities),
                    "tools": [
                        {
                            "name": capability.name,
                            "description": capability.description,
                            "permissions": sorted(capability.permissions),
                        }
                        for capability in agent.tool_capabilities
                    ],
                }
                for agent in self.runtime.available_agents()
            ],
            "prompt_policy": "system prompts are not exposed by the API",
        }

    def scheduler(self) -> dict[str, Any]:
        return self.runtime.components.scheduler.snapshot().as_dict()

    def hardware(self) -> dict[str, Any]:
        profiler = self.runtime.components.hardware_profiler
        if profiler is None:
            raise ConfigurationError("hardware profiler is not configured")
        return profiler.snapshot().as_dict()

    def models(self) -> dict[str, Any]:
        registry, budgets = load_model_registry(self._model_registry_path)
        models: list[dict[str, Any]] = []
        for model in registry.models:
            item = model.as_dict()
            item["artifact"] = Path(item.pop("path")).name
            models.append(item)
        return {
            "models": models,
            "notes": list(registry.notes),
            "compute_budgets": {
                workload.value: budget.as_dict()
                for workload, budget in budgets.workload_budgets.items()
            },
        }

    def metrics(self, query: dict[str, str]) -> dict[str, Any]:
        backend = self.runtime.components.observability
        if backend is None:
            raise ConfigurationError("observability backend is not configured")
        unexpected = set(query) - {"window_minutes", "task_limit", "event_limit", "live"}
        if unexpected:
            raise ApiRequestError("unknown metrics query parameter", details={"fields": sorted(unexpected)})
        live_value = query.get("live", "true").lower()
        if live_value not in {"true", "false"}:
            raise ApiRequestError("live query parameter must be true or false")
        return backend.report(
            window_minutes=_positive_query(query.get("window_minutes"), "window_minutes"),
            recent_task_limit=_positive_query(query.get("task_limit"), "task_limit"),
            recent_event_limit=_positive_query(query.get("event_limit"), "event_limit"),
            include_live=live_value == "true",
        ).as_dict()

    def chaos(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._exact_fields(payload, {"confirm", "scenarios"}, required={"confirm", "scenarios"})
        if payload["confirm"] is not True:
            raise ApiRequestError("chaos execution requires confirm=true")
        scenarios = payload["scenarios"]
        if (
            not isinstance(scenarios, list)
            or not scenarios
            or any(not isinstance(value, str) or not value.strip() for value in scenarios)
            or len(set(scenarios)) != len(scenarios)
            or len(scenarios) > self.config.max_chaos_scenarios_per_request
        ):
            raise ApiRequestError(
                "scenarios must be a bounded non-empty list of unique IDs",
                details={"maximum": self.config.max_chaos_scenarios_per_request},
            )
        self._chaos_data_directory.mkdir(parents=True, exist_ok=True)
        database = self._chaos_data_directory / f"stage15-api-chaos-{uuid4().hex}.db"
        report = run_chaos_suite(database, self._chaos_config_path, tuple(scenarios))
        return {
            "isolation": "separate stub runtime and unique SQLite database; serving runtime unchanged",
            "report": report,
        }

    def security_results(self) -> dict[str, Any]:
        directory = self.config.security_results_directory
        matches = sorted(directory.glob("stage14-security-*.json"), reverse=True)
        if not matches:
            raise TaskNotFoundError(
                "no retained Stage 14 security result is available",
                details={"directory": str(directory)},
            )
        selected = matches[0].resolve()
        try:
            selected.relative_to(directory.resolve())
        except ValueError as error:
            raise ConfigurationError("security result resolved outside its configured directory") from error
        try:
            report = json.loads(selected.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigurationError(
                "retained security result could not be read",
                details={"cause_type": type(error).__name__},
            ) from error
        return {
            "result_id": selected.stem,
            "report": report,
            "scope": "retained deterministic Stage 14 adversarial evidence; not a production penetration test",
        }

    @staticmethod
    def _exact_fields(payload: dict[str, Any], allowed: set[str], *, required: set[str]) -> None:
        missing = required - set(payload)
        unexpected = set(payload) - allowed
        if missing or unexpected:
            raise ApiRequestError(
                "request object fields are invalid",
                details={"missing": sorted(missing), "unexpected": sorted(unexpected)},
            )

    def shutdown(self) -> None:
        self.tasks.shutdown()
