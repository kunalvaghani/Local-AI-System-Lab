"""SQLite persistence, recovery, and Stage 11 trace schema."""

from .config import PersistenceConfig, load_persistence_config
from .models import RecoveryAttempt, RecoveryCandidate, RecoveryDisposition
from .sqlite_store import SCHEMA_VERSION, SQLiteRuntimeStore
from .adapters import (
    SQLiteAgentRegistry,
    SQLiteCheckpointStore,
    SQLiteLifecycleEventStore,
    SQLiteMetricsCollector,
    SQLiteTaskStateMachine,
)

__all__ = [
    "PersistenceConfig",
    "RecoveryAttempt",
    "RecoveryCandidate",
    "RecoveryDisposition",
    "SCHEMA_VERSION",
    "SQLiteRuntimeStore",
    "SQLiteAgentRegistry",
    "SQLiteCheckpointStore",
    "SQLiteLifecycleEventStore",
    "SQLiteMetricsCollector",
    "SQLiteTaskStateMachine",
    "load_persistence_config",
]
