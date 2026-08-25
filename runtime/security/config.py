"""Strict Stage 14 security-policy configuration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ConfigurationError


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"security {name} must be an object")
    return value


def _positive(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"security {name} must be a positive integer")
    return value


def _strings(value: Any, name: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ConfigurationError(f"security {name} must be a non-empty string list")
    if len(value) != len(set(value)):
        raise ConfigurationError(f"security {name} entries must be unique")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    max_objective_characters: int
    max_payload_depth: int
    max_payload_nodes: int
    max_string_characters: int
    max_output_characters: int
    max_tool_result_characters: int
    max_subprocess_arguments: int
    max_subprocess_command_characters: int
    max_processes: int
    max_timeout_ms: int
    allowed_entries: tuple[str, ...]
    denied_components: tuple[str, ...]
    allowed_suffixes: tuple[str, ...]
    allowed_permissions: frozenset[str]
    require_read_only: bool
    require_path_restriction_for_filesystem: bool
    network_default: str
    sensitive_key_fragments: tuple[str, ...]
    secret_patterns: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.network_default != "deny":
            raise ConfigurationError("Stage 14 network.default must be deny")
        if any(not suffix.startswith(".") for suffix in self.allowed_suffixes):
            raise ConfigurationError("allowed path suffixes must begin with a dot")
        for pattern in self.secret_patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                raise ConfigurationError(
                    "security secret pattern is invalid",
                    details={"pattern": pattern},
                ) from error


def load_security_config(path: str | Path = "configs/security.json") -> SecurityConfig:
    config_path = Path(path).resolve()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "failed to read security configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
    if data.get("schema_version") != 1:
        raise ConfigurationError("unsupported security configuration schema")
    allowed_root_keys = {"schema_version", "limits", "paths", "tools", "network", "secrets"}
    if set(data) != allowed_root_keys:
        raise ConfigurationError(
            "security configuration has missing or unknown root fields",
            details={"fields": sorted(data)},
        )
    limits = _object(data["limits"], "limits")
    paths = _object(data["paths"], "paths")
    tools = _object(data["tools"], "tools")
    network = _object(data["network"], "network")
    secrets = _object(data["secrets"], "secrets")
    expected_limits = {
        "max_objective_characters", "max_payload_depth", "max_payload_nodes",
        "max_string_characters", "max_output_characters", "max_tool_result_characters",
        "max_subprocess_arguments", "max_subprocess_command_characters",
        "max_processes", "max_timeout_ms",
    }
    if set(limits) != expected_limits:
        raise ConfigurationError("security limits have missing or unknown fields")
    if set(paths) != {"allowed_entries", "denied_components", "allowed_suffixes"}:
        raise ConfigurationError("security paths have missing or unknown fields")
    if set(tools) != {
        "allowed_permissions",
        "require_read_only",
        "require_path_restriction_for_filesystem",
    }:
        raise ConfigurationError("security tools have missing or unknown fields")
    if set(network) != {"default"}:
        raise ConfigurationError("security network has missing or unknown fields")
    if set(secrets) != {"sensitive_key_fragments", "patterns"}:
        raise ConfigurationError("security secrets have missing or unknown fields")
    if not isinstance(tools.get("require_read_only"), bool) or not isinstance(
        tools.get("require_path_restriction_for_filesystem"), bool
    ):
        raise ConfigurationError("security tool switches must be booleans")
    return SecurityConfig(
        **{name: _positive(limits[name], name) for name in expected_limits},
        allowed_entries=_strings(paths.get("allowed_entries"), "paths.allowed_entries"),
        denied_components=_strings(paths.get("denied_components"), "paths.denied_components"),
        allowed_suffixes=_strings(paths.get("allowed_suffixes"), "paths.allowed_suffixes"),
        allowed_permissions=frozenset(_strings(tools.get("allowed_permissions"), "tools.allowed_permissions")),
        require_read_only=tools["require_read_only"],
        require_path_restriction_for_filesystem=tools["require_path_restriction_for_filesystem"],
        network_default=str(network.get("default", "")),
        sensitive_key_fragments=_strings(secrets.get("sensitive_key_fragments"), "secrets.sensitive_key_fragments"),
        secret_patterns=_strings(secrets.get("patterns"), "secrets.patterns"),
    )
