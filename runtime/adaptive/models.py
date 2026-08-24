"""Typed Stage 8 profile catalog and selection evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..hardware import AdmissionDecision, HardwareSnapshot
from ..models import InferenceProfile
from ..routing import ComputeBudget
from ..scheduler import WorkloadClass


@dataclass(frozen=True, slots=True)
class ProfileAttempt:
    profile: InferenceProfile
    admission: AdmissionDecision
    budget_constraints: tuple[str, ...] = tuple()

    @property
    def eligible(self) -> bool:
        return self.admission.permitted and not self.budget_constraints

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.as_dict(),
            "admission": self.admission.as_dict(),
            "budget_constraints": list(self.budget_constraints),
            "eligible": self.eligible,
        }


@dataclass(frozen=True, slots=True)
class ProfileSelection:
    workload: WorkloadClass
    selected_profile: InferenceProfile | None
    admission: AdmissionDecision
    hardware: HardwareSnapshot
    reason: str
    attempts: tuple[ProfileAttempt, ...]
    budget: ComputeBudget | None = None

    @property
    def permitted(self) -> bool:
        return self.selected_profile is not None and self.admission.permitted

    @property
    def budget_limited(self) -> bool:
        return self.selected_profile is None and any(
            attempt.budget_constraints for attempt in self.attempts
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "workload": self.workload.value,
            "permitted": self.permitted,
            "selected_profile": (
                self.selected_profile.as_dict()
                if self.selected_profile is not None
                else None
            ),
            "admission": self.admission.as_dict(),
            "hardware": self.hardware.as_dict(),
            "reason": self.reason,
            "attempts": [attempt.as_dict() for attempt in self.attempts],
            "budget": self.budget.as_dict() if self.budget is not None else None,
            "budget_limited": self.budget_limited,
        }
