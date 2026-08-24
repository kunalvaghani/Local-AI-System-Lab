"""Evidence-backed adaptive profile selection with mandatory re-admission."""

from __future__ import annotations

from ..hardware import (
    AdmissionPolicy,
    AdmissionRequest,
    ConservativeMemoryEstimator,
    LocalHardwareProfiler,
)
from ..hardware.config import AdmissionConfig
from ..models import Task
from ..scheduler import SchedulingOptions
from ..routing import ComputeBudget
from .config import InferenceProfileCatalog
from .models import ProfileAttempt, ProfileSelection


class AdaptiveInferenceController:
    def __init__(
        self,
        catalog: InferenceProfileCatalog,
        admission_config: AdmissionConfig,
        profiler: LocalHardwareProfiler | None = None,
    ) -> None:
        self.catalog = catalog
        self.admission_config = admission_config
        self.profiler = profiler or LocalHardwareProfiler()
        self.estimator = ConservativeMemoryEstimator(admission_config.estimator)
        self.policy = AdmissionPolicy(self.estimator)
        self.last_selection: ProfileSelection | None = None

    def select(
        self,
        task: Task,
        scheduling: SchedulingOptions,
        budget: ComputeBudget | None = None,
    ) -> ProfileSelection:
        hardware = self.profiler.snapshot()
        attempts: list[ProfileAttempt] = []
        selected = None
        for profile_id in self.catalog.workload_order[scheduling.workload]:
            profile = self.catalog.get(profile_id)
            admission = self.policy.evaluate(
                AdmissionRequest(
                    model=self.admission_config.model,
                    context_tokens=profile.context_size,
                    gpu_layers=profile.gpu_layers,
                    workload=scheduling.workload,
                    allow_context_reduction=False,
                    allow_gpu_reduction=False,
                ),
                hardware,
            )
            budget_constraints: list[str] = []
            if budget is not None:
                if (
                    budget.max_ram_mib is not None
                    and admission.estimate.predicted_host_ram_mib > budget.max_ram_mib
                ):
                    budget_constraints.append("predicted host RAM exceeds max_ram_mib")
                if (
                    budget.max_vram_mib is not None
                    and admission.estimate.predicted_vram_mib > budget.max_vram_mib
                ):
                    budget_constraints.append("predicted VRAM exceeds max_vram_mib")
            attempt = ProfileAttempt(profile, admission, tuple(budget_constraints))
            attempts.append(attempt)
            if attempt.eligible:
                selected = profile
                break
        final_admission = attempts[-1].admission
        if selected is None:
            reason = (
                "no configured resource profile passed live memory admission and task budget constraints"
            )
        else:
            reason = (
                f"selected {selected.profile_id} as the first admitted "
                f"{scheduling.workload.value} profile"
            )
        selection = ProfileSelection(
            workload=scheduling.workload,
            selected_profile=selected,
            admission=final_admission,
            hardware=hardware,
            reason=reason,
            attempts=tuple(attempts),
            budget=budget,
        )
        self.last_selection = selection
        return selection
