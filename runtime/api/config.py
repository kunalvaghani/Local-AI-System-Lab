"""Strict loopback API configuration for Stage 15."""

from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


def _integer(value: Any, name: str, *, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ConfigurationError(f"API {name} must be a {qualifier} integer")
    return value


@dataclass(frozen=True, slots=True)
class ApiConfig:
    host: str
    port: int
    max_request_bytes: int
    max_inflight_tasks: int
    default_task_timeout_ms: int
    max_task_timeout_ms: int
    stream_poll_ms: int
    stream_timeout_ms: int
    max_chaos_scenarios_per_request: int
    security_results_directory: Path

    def __post_init__(self) -> None:
        try:
            address = ipaddress.ip_address(self.host)
        except ValueError as error:
            raise ConfigurationError("API host must be a literal loopback IP address") from error
        if not address.is_loopback:
            raise ConfigurationError("Stage 15 API must bind to a loopback address")
        if not 0 <= self.port <= 65_535:
            raise ConfigurationError("API port must be between 0 and 65535")
        if self.default_task_timeout_ms > self.max_task_timeout_ms:
            raise ConfigurationError("default API task timeout exceeds the maximum")
        if self.stream_poll_ms > self.stream_timeout_ms:
            raise ConfigurationError("API stream polling interval exceeds stream timeout")


def load_api_config(path: str | Path = "configs/api.json") -> ApiConfig:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "failed to read API configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
    if not isinstance(payload, dict):
        raise ConfigurationError("API configuration must be a JSON object")
    expected = {
        "schema_version",
        "host",
        "port",
        "max_request_bytes",
        "max_inflight_tasks",
        "default_task_timeout_ms",
        "max_task_timeout_ms",
        "stream_poll_ms",
        "stream_timeout_ms",
        "max_chaos_scenarios_per_request",
        "security_results_directory",
    }
    if set(payload) != expected or payload.get("schema_version") != 1:
        raise ConfigurationError("API configuration schema or fields are invalid")
    directory = payload["security_results_directory"]
    if not isinstance(directory, str) or not directory.strip():
        raise ConfigurationError("API security results directory must be a path string")
    root = config_path.parent.parent
    return ApiConfig(
        host=str(payload["host"]),
        port=_integer(payload["port"], "port", allow_zero=True),
        max_request_bytes=_integer(payload["max_request_bytes"], "max_request_bytes"),
        max_inflight_tasks=_integer(payload["max_inflight_tasks"], "max_inflight_tasks"),
        default_task_timeout_ms=_integer(payload["default_task_timeout_ms"], "default_task_timeout_ms"),
        max_task_timeout_ms=_integer(payload["max_task_timeout_ms"], "max_task_timeout_ms"),
        stream_poll_ms=_integer(payload["stream_poll_ms"], "stream_poll_ms"),
        stream_timeout_ms=_integer(payload["stream_timeout_ms"], "stream_timeout_ms"),
        max_chaos_scenarios_per_request=_integer(
            payload["max_chaos_scenarios_per_request"],
            "max_chaos_scenarios_per_request",
        ),
        security_results_directory=(root / directory).resolve(),
    )
