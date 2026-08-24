"""Inspect live hardware, memory estimates, calibration, and admission outcomes."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from typing import Any

from .errors import LabError
from .hardware import (
    AdmissionPolicy,
    AdmissionRequest,
    Confidence,
    ConservativeMemoryEstimator,
    CpuSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    LocalHardwareProfiler,
    ModelMemoryProfile,
    RamSnapshot,
    load_admission_config,
)
from .scheduler import WorkloadClass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile this host and make conservative Stage 7 admission decisions.",
    )
    parser.add_argument(
        "--config",
        default="configs/admission-baseline.json",
        help="Validated model metadata, estimator coefficients, and calibration evidence.",
    )
    return parser


def _synthetic_hardware(*, free_vram: float, total_vram: float = 4096.0) -> HardwareSnapshot:
    return HardwareSnapshot(
        cpu=CpuSnapshot("controlled CPU", 16, 8, "controlled fixture", Confidence.HIGH),
        ram=RamSnapshot(32768.0, 12000.0, 20768.0, "controlled fixture", Confidence.HIGH),
        gpu=GpuSnapshot(
            "controlled GPU",
            "fixture",
            total_vram,
            total_vram - free_vram,
            free_vram,
            0.0,
            40.0,
            "fixture",
            "controlled fixture",
            Confidence.HIGH,
        ),
        warnings=("synthetic snapshot; this is policy coverage, not live telemetry",),
    )


def controlled_decisions(config: Any, policy: AdmissionPolicy) -> dict[str, Any]:
    base = AdmissionRequest(
        config.model,
        config.model.baseline_context_tokens,
        config.model.baseline_gpu_layers,
    )
    fallback = ModelMemoryProfile(
        model_id="controlled/smaller-fallback",
        path="synthetic",
        file_size_mib=200.0,
        quantization="controlled",
        layer_count=12,
        baseline_context_tokens=1024,
        baseline_gpu_layers=12,
    )
    cases = {
        "ACCEPT": (base, _synthetic_hardware(free_vram=4000.0)),
        "QUEUE": (
            replace(base, workload=WorkloadClass.BACKGROUND),
            _synthetic_hardware(free_vram=1000.0),
        ),
        "REDUCE_CONTEXT": (base, _synthetic_hardware(free_vram=1710.0)),
        "REDUCE_GPU_OFFLOAD": (base, _synthetic_hardware(free_vram=1000.0)),
        "FALLBACK": (
            replace(
                base,
                allow_context_reduction=False,
                allow_gpu_reduction=False,
                fallback_model=fallback,
            ),
            _synthetic_hardware(free_vram=1500.0, total_vram=1500.0),
        ),
        "REJECT_UNSAFE": (
            replace(
                base,
                allow_context_reduction=False,
                allow_gpu_reduction=False,
            ),
            _synthetic_hardware(free_vram=1000.0, total_vram=1000.0),
        ),
    }
    return {
        expected: {
            "source": "controlled synthetic policy scenario",
            **policy.evaluate(request, hardware).as_dict(),
        }
        for expected, (request, hardware) in cases.items()
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_admission_config(args.config)
        estimator = ConservativeMemoryEstimator(config.estimator)
        policy = AdmissionPolicy(estimator)
        request = AdmissionRequest(
            config.model,
            config.model.baseline_context_tokens,
            config.model.baseline_gpu_layers,
        )
        snapshot = LocalHardwareProfiler().snapshot()
        decision = policy.evaluate(request, snapshot)
        comparison = estimator.compare_calibration(request, config.calibration)
        print(
            json.dumps(
                {
                    "stage": 7,
                    "purpose": "inspect resources and stop unsafe workloads before scheduling",
                    "hardware": snapshot.as_dict(),
                    "model": {
                        "id": config.model.model_id,
                        "path": config.model.path,
                        "file_size_mib": round(config.model.file_size_mib, 3),
                        "quantization": config.model.quantization,
                        "layer_count": config.model.layer_count,
                        "context_tokens": config.model.baseline_context_tokens,
                        "gpu_layers": config.model.baseline_gpu_layers,
                    },
                    "estimate": estimator.estimate(request).as_dict(),
                    "calibration_comparison": comparison.as_dict(),
                    "live_admission": decision.as_dict(),
                    "controlled_policy_demonstration": controlled_decisions(config, policy),
                    "boundary": (
                        "Only ACCEPT executes in Stage 7. Other actions require resubmission "
                        "after the indicated adaptation or pressure change."
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except LabError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
