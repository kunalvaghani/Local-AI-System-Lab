"""Strict file-backed configuration for bounded Stage 13 fault plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError
from .models import FaultKind, FaultPlan, FaultScenario


@dataclass(frozen=True, slots=True)
class ChaosConfig:
    enabled: bool
    max_delay_ms: int
    scenarios: tuple[FaultScenario, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise ConfigurationError("chaos enabled must be boolean")
        if (
            isinstance(self.max_delay_ms, bool)
            or not isinstance(self.max_delay_ms, int)
            or self.max_delay_ms < 0
        ):
            raise ConfigurationError("chaos max_delay_ms must be a non-negative integer")
        if not self.scenarios:
            raise ConfigurationError("chaos configuration requires at least one scenario")
        if any(item.delay_ms > self.max_delay_ms for item in self.scenarios):
            raise ConfigurationError("fault delay exceeds chaos max_delay_ms")
        FaultPlan(False, self.scenarios)

    def plan(
        self,
        *,
        armed: bool | None = None,
        scenario_ids: tuple[str, ...] | None = None,
    ) -> FaultPlan:
        selected = self.scenarios
        if scenario_ids is not None:
            requested = set(scenario_ids)
            selected = tuple(item for item in self.scenarios if item.scenario_id in requested)
            missing = requested - {item.scenario_id for item in selected}
            if missing:
                raise ConfigurationError(
                    "unknown fault scenario requested",
                    details={"scenario_ids": sorted(missing)},
                )
        return FaultPlan(
            armed=self.enabled if armed is None else armed,
            scenarios=selected,
        )


def load_chaos_config(path: str | Path = "configs/chaos.json") -> ChaosConfig:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ConfigurationError("unsupported chaos configuration schema")
        raw_scenarios = payload.get("scenarios")
        if not isinstance(raw_scenarios, list):
            raise ConfigurationError("chaos scenarios must be a list")
        scenarios: list[FaultScenario] = []
        for raw in raw_scenarios:
            if not isinstance(raw, dict):
                raise ConfigurationError("each chaos scenario must be an object")
            scenarios.append(
                FaultScenario(
                    scenario_id=raw.get("scenario_id"),
                    kind=FaultKind(raw.get("kind")),
                    delay_ms=raw.get("delay_ms", 0),
                    max_injections=raw.get("max_injections", 1),
                )
            )
        return ChaosConfig(
            enabled=payload.get("enabled", False),
            max_delay_ms=payload.get("max_delay_ms", 1000),
            scenarios=tuple(scenarios),
        )
    except ConfigurationError:
        raise
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "could not load chaos configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
