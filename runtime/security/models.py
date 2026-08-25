"""Typed Stage 14 security and adversarial-test evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class SecurityCaseResult:
    case_id: str
    category: str
    expected: str
    actual: str
    passed: bool
    duration_ms: float
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "status": "PASS" if self.passed else "FAIL",
            "expected": self.expected,
            "actual": self.actual,
            "duration_ms": self.duration_ms,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class SecurityReport:
    cases: tuple[SecurityCaseResult, ...]
    database: str
    integrity_check: str
    real_llm_calls: int
    generated_at_utc: str = field(default_factory=utc_now_iso)

    @property
    def passed(self) -> int:
        return sum(case.passed for case in self.cases)

    def as_dict(self) -> dict[str, Any]:
        durations = [case.duration_ms for case in self.cases]
        return {
            "stage": 14,
            "purpose": "repeatable security and adversarial testing with evidence",
            "disclaimer": (
                "Passing these bounded tests does not prove the system is secure."
            ),
            "generated_at_utc": self.generated_at_utc,
            "database": self.database,
            "summary": {
                "cases": len(self.cases),
                "passed": self.passed,
                "failed": len(self.cases) - self.passed,
                "pass_rate_percent": (
                    round(self.passed / len(self.cases) * 100.0, 6)
                    if self.cases
                    else None
                ),
                "total_duration_ms": round(sum(durations), 6),
                "real_llm_calls": self.real_llm_calls,
                "integrity_check": self.integrity_check,
            },
            "cases": [case.as_dict() for case in self.cases],
        }
