"""Configurable, bounded fault injection introduced in Stage 13."""

from .adapters import (
    FaultInjectingInferenceBackend,
    FaultInjectingPersistence,
    FaultInjectingToolExecutor,
)
from .config import ChaosConfig, load_chaos_config
from .controller import FaultController
from .models import (
    ChaosReport,
    ChaosScenarioResult,
    FaultKind,
    FaultPlan,
    FaultPoint,
    FaultRecord,
    FaultScenario,
)
from .runner import EXPECTED, execute_fault_scenario

__all__ = [
    "ChaosConfig",
    "ChaosReport",
    "ChaosScenarioResult",
    "FaultController",
    "FaultInjectingInferenceBackend",
    "FaultInjectingPersistence",
    "FaultInjectingToolExecutor",
    "FaultKind",
    "FaultPlan",
    "FaultPoint",
    "FaultRecord",
    "FaultScenario",
    "load_chaos_config",
    "EXPECTED",
    "execute_fault_scenario",
]
