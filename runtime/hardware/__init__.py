"""Hardware profiling and conservative memory admission from Stage 7."""

from .admission import AdmissionPolicy, MemoryAwareAdmissionGate
from .config import AdmissionConfig, CalibrationRecord, EstimatorConfig, load_admission_config
from .estimator import ConservativeMemoryEstimator
from .models import (
    AdmissionAction,
    AdmissionDecision,
    AdmissionRequest,
    CalibrationComparison,
    Confidence,
    CpuSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    MemoryEstimate,
    ModelMemoryProfile,
    RamSnapshot,
)
from .profiler import LocalHardwareProfiler

__all__ = [
    "AdmissionAction",
    "AdmissionConfig",
    "AdmissionDecision",
    "AdmissionPolicy",
    "AdmissionRequest",
    "CalibrationComparison",
    "CalibrationRecord",
    "Confidence",
    "ConservativeMemoryEstimator",
    "CpuSnapshot",
    "EstimatorConfig",
    "GpuSnapshot",
    "HardwareSnapshot",
    "LocalHardwareProfiler",
    "MemoryAwareAdmissionGate",
    "MemoryEstimate",
    "ModelMemoryProfile",
    "RamSnapshot",
    "load_admission_config",
]
