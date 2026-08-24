"""Inspect Stage 8 adaptive profile selection without launching a model."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace

from .adaptive import AdaptiveInferenceController, load_inference_profile_catalog
from .errors import LabError
from .hardware import Confidence, HardwareSnapshot, LocalHardwareProfiler, RamSnapshot
from .hardware.config import load_admission_config
from .models import Task, utc_now
from .scheduler import SchedulingOptions, WorkloadClass


class _FixedProfiler:
    def __init__(self, snapshot: HardwareSnapshot) -> None:
        self.snapshot_value = snapshot

    def snapshot(self) -> HardwareSnapshot:
        return self.snapshot_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect adaptive llama.cpp profile selection and re-admission.",
    )
    parser.add_argument("--profiles", default="configs/inference-profiles.json")
    parser.add_argument("--admission", default="configs/admission-baseline.json")
    return parser


def _select(
    controller: AdaptiveInferenceController,
    workload: WorkloadClass,
) -> dict[str, object]:
    task = Task(
        task_id=f"adaptive-cli-{workload.value}",
        agent_id="adaptive-cli",
        objective="Inspect profile selection",
        created_at=utc_now(),
    )
    return controller.select(task, SchedulingOptions(workload=workload)).as_dict()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_inference_profile_catalog(args.profiles)
        admission = load_admission_config(args.admission)
        live_snapshot = LocalHardwareProfiler().snapshot()
        live = {
            workload.value: _select(
                AdaptiveInferenceController(
                    catalog,
                    admission,
                    _FixedProfiler(live_snapshot),  # type: ignore[arg-type]
                ),
                workload,
            )
            for workload in WorkloadClass
        }
        gpu_pressure = replace(
            live_snapshot,
            gpu=(
                replace(live_snapshot.gpu, used_vram_mib=2596.0, free_vram_mib=1500.0)
                if live_snapshot.gpu is not None
                else None
            ),
            warnings=live_snapshot.warnings
            + ("controlled 1500 MiB free-VRAM scenario",),
        )
        missing_ram = replace(
            live_snapshot,
            ram=RamSnapshot(None, None, None, "controlled unavailable", Confidence.UNAVAILABLE),
            warnings=live_snapshot.warnings + ("controlled missing-RAM scenario",),
        )
        missing_gpu = replace(
            live_snapshot,
            gpu=None,
            warnings=live_snapshot.warnings + ("controlled missing-GPU scenario",),
        )
        controlled = {
            "gpu_pressure": _select(
                AdaptiveInferenceController(
                    catalog,
                    admission,
                    _FixedProfiler(gpu_pressure),  # type: ignore[arg-type]
                ),
                WorkloadClass.STANDARD,
            ),
            "missing_ram": _select(
                AdaptiveInferenceController(
                    catalog,
                    admission,
                    _FixedProfiler(missing_ram),  # type: ignore[arg-type]
                ),
                WorkloadClass.STANDARD,
            ),
            "missing_gpu": _select(
                AdaptiveInferenceController(
                    catalog,
                    admission,
                    _FixedProfiler(missing_gpu),  # type: ignore[arg-type]
                ),
                WorkloadClass.STANDARD,
            ),
        }
        print(
            json.dumps(
                {
                    "stage": 8,
                    "purpose": "select and re-admit explicit llama.cpp resource profiles",
                    "profiles": [profile.as_dict() for profile in catalog.profiles],
                    "selection_notes": list(catalog.selection_notes),
                    "live_selection": live,
                    "controlled_selection": controlled,
                    "boundary": "This Stage 8 view adapts one pinned model; use runtime.routing_cli for Stage 9 model routing.",
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
