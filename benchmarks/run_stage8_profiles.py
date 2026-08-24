"""Run the same real workload through each Stage 8 resource profile."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.adaptive import load_inference_profile_catalog
from runtime.hardware import (
    AdmissionPolicy,
    AdmissionRequest,
    ConservativeMemoryEstimator,
    LocalHardwareProfiler,
    load_admission_config,
)
from runtime.inference import LlamaCppCompletionBackend, load_llama_cpp_config
from runtime.models import InferenceRequest
from runtime.scheduler import WorkloadClass


PROMPT = (
    "In exactly two short sentences, explain one benefit and one limitation "
    "of running a language model locally."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inference", default="configs/inference-baseline.json")
    parser.add_argument("--admission", default="configs/admission-baseline.json")
    parser.add_argument("--profiles", default="configs/inference-profiles.json")
    parser.add_argument("--profile", action="append", default=None)
    parser.add_argument("--runs-per-profile", type=int, default=1)
    parser.add_argument("--output", default=None)
    return parser


def _summary(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    fields = (
        "model_load_ms",
        "ttft_ms",
        "prompt_eval_ms",
        "tokens_per_second",
        "total_ms",
        "peak_process_ram_mib",
        "vram_delta_mib",
    )
    result: dict[str, dict[str, float]] = {}
    for profile_id in sorted({record["profile_id"] for record in records}):
        profile_records = [record for record in records if record["profile_id"] == profile_id]
        result[profile_id] = {}
        for field in fields:
            values = [
                float(record["metrics"][field])
                for record in profile_records
                if record["metrics"].get(field) is not None
            ]
            if values:
                result[profile_id][field] = statistics.fmean(values)
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runs_per_profile <= 0:
        raise SystemExit("--runs-per-profile must be positive")
    inference = load_llama_cpp_config(args.inference)
    admission = load_admission_config(args.admission)
    catalog = load_inference_profile_catalog(args.profiles)
    profile_ids = args.profile or [profile.profile_id for profile in catalog.profiles]
    selected = [catalog.get(profile_id) for profile_id in profile_ids]
    estimator = ConservativeMemoryEstimator(admission.estimator)
    policy = AdmissionPolicy(estimator)
    profiler = LocalHardwareProfiler()
    backend = LlamaCppCompletionBackend(inference)
    records: list[dict[str, Any]] = []
    captured_at = datetime.now(timezone.utc)
    try:
        backend.start()
        for profile in selected:
            for iteration in range(1, args.runs_per_profile + 1):
                hardware = profiler.snapshot()
                admission_request = AdmissionRequest(
                    admission.model,
                    profile.context_size,
                    profile.gpu_layers,
                    workload=WorkloadClass.STANDARD,
                    allow_context_reduction=False,
                    allow_gpu_reduction=False,
                )
                decision = policy.evaluate(admission_request, hardware)
                if not decision.permitted:
                    raise SystemExit(
                        f"profile {profile.profile_id} was not admitted: {decision.action.value}"
                    )
                result = backend.generate(
                    InferenceRequest(
                        task_id=f"stage8-{profile.profile_id}-{iteration}",
                        prompt=PROMPT,
                        model_id=inference.model_id,
                        max_generated_tokens=32,
                        profile=profile,
                    )
                )
                record = {
                    "profile_id": profile.profile_id,
                    "iteration": iteration,
                    "profile": profile.as_dict(),
                    "admission": decision.as_dict(),
                    "hardware_before": hardware.as_dict(),
                    "prompt": PROMPT,
                    "output": result.text,
                    "metrics": result.metrics.as_dict() if result.metrics else {},
                }
                records.append(record)
                metrics = record["metrics"]
                print(
                    f"{profile.profile_id}#{iteration}: "
                    f"TTFT={metrics.get('ttft_ms')} ms, "
                    f"generation={metrics.get('tokens_per_second')} tok/s, "
                    f"VRAM={metrics.get('vram_delta_mib')} MiB"
                )
    finally:
        backend.shutdown()

    summary = _summary(records)
    measured_profiles = list(summary)
    observations = {
        "lowest_observed_ttft": min(
            measured_profiles, key=lambda name: summary[name]["ttft_ms"]
        ),
        "highest_observed_generation_rate": max(
            measured_profiles, key=lambda name: summary[name]["tokens_per_second"]
        ),
        "lowest_observed_vram_delta": min(
            measured_profiles, key=lambda name: summary[name].get("vram_delta_mib", float("inf"))
        ),
        "claim_boundary": (
            "These are observations from this declared sample, not universal or optimal settings."
        ),
    }
    output = (
        Path(args.output)
        if args.output
        else Path("benchmarks/results")
        / f"stage8-profile-comparison-{captured_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    payload = {
        "schema_version": 1,
        "captured_at_utc": captured_at.isoformat(),
        "workload": {
            "prompt": PROMPT,
            "max_generated_tokens": 32,
            "runs_per_profile": args.runs_per_profile,
        },
        "model_id": inference.model_id,
        "backend_release": inference.release,
        "profiles": profile_ids,
        "records": records,
        "summary_mean": summary,
        "observations": observations,
        "measurement_notes": [
            "The same prompt, token cap, seed, model, backend build, and sampling path are used.",
            "Each sample is a cold one-process model load.",
            "One run per profile demonstrates behavior but is not statistically strong.",
            "VRAM is sampled device-wide at 200 ms and may include unrelated allocations.",
            "Several profile parameters change together, so the comparison does not attribute causality to one flag.",
        ],
    }
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
