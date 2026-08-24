"""Validated SQLite persistence configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class PersistenceConfig:
    database_path: Path
    busy_timeout_ms: int = 5000
    journal_mode: str = "WAL"
    synchronous: str = "FULL"

    def __post_init__(self) -> None:
        if self.busy_timeout_ms <= 0:
            raise ConfigurationError("persistence busy_timeout_ms must be positive")
        if self.journal_mode not in {"WAL", "DELETE"}:
            raise ConfigurationError("persistence journal_mode must be WAL or DELETE")
        if self.synchronous not in {"FULL", "NORMAL"}:
            raise ConfigurationError("persistence synchronous must be FULL or NORMAL")


def load_persistence_config(
    path: str | Path = "configs/persistence.json",
) -> PersistenceConfig:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ConfigurationError("unsupported persistence configuration schema")
        return PersistenceConfig(
            database_path=(config_path.parent.parent / str(payload["database_path"])).resolve(),
            busy_timeout_ms=int(payload.get("busy_timeout_ms", 5000)),
            journal_mode=str(payload.get("journal_mode", "WAL")).upper(),
            synchronous=str(payload.get("synchronous", "FULL")).upper(),
        )
    except ConfigurationError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "could not load persistence configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
