"""Validated Stage 12 observability report configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class ObservabilityConfig:
    default_window_minutes: int = 60
    recent_task_limit: int = 50
    recent_event_limit: int = 100
    include_live_hardware: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("default_window_minutes", self.default_window_minutes),
            ("recent_task_limit", self.recent_task_limit),
            ("recent_event_limit", self.recent_event_limit),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ConfigurationError(f"observability {name} must be a positive integer")
        if not isinstance(self.include_live_hardware, bool):
            raise ConfigurationError("observability include_live_hardware must be boolean")


def load_observability_config(
    path: str | Path = "configs/observability.json",
) -> ObservabilityConfig:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ConfigurationError("unsupported observability configuration schema")
        return ObservabilityConfig(
            default_window_minutes=payload.get("default_window_minutes", 60),
            recent_task_limit=payload.get("recent_task_limit", 50),
            recent_event_limit=payload.get("recent_event_limit", 100),
            include_live_hardware=payload.get("include_live_hardware", True),
        )
    except ConfigurationError:
        raise
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "could not load observability configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
