"""Run and store the reproducible Stage 2 local inference baseline."""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.inference import LlamaCppCompletionBackend, load_llama_cpp_config
from runtime.models import InferenceRequest


METRIC_FIELDS = (
    "model_load_ms",
    "startup_to_ready_ms",
    "ttft_ms",
    "prompt_eval_ms",
    "prompt_tokens_per_second",
    "generation_ms",
    "tokens_per_second",
    "total_ms",
    "peak_process_ram_mib",
    "vram_delta_mib",
)


def _percentile_nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _summarize(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for field in METRIC_FIELDS:
        values = [
            float(record["metrics"][field])
            for record in records
            if record["metrics"].get(field) is not None
        ]
        if not values:
            continue
        summary[field] = {
            "count": len(values),
            "min": min(values),
            "mean": statistics.fmean(values),
            "p50": statistics.median(values),
            "p95_nearest_rank": _percentile_nearest_rank(values, 0.95),
            "max": max(values),
        }
    return summary


def _command_output(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (completed.stdout or completed.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/inference-baseline.json")
    parser.add_argument("--prompts", default="benchmarks/prompts/stage2-baseline.json")
    parser.add_argument("--runs-per-prompt", type=int, default=1)
    parser.add_argument("--output", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.runs_per_prompt <= 0:
        raise SystemExit("--runs-per-prompt must be greater than zero")

    config = load_llama_cpp_config(args.config)
    prompt_data = json.loads(Path(args.prompts).read_text(encoding="utf-8"))
    if prompt_data.get("schema_version") != 1:
        raise SystemExit("unsupported prompt workload schema")

    captured_at = datetime.now(timezone.utc)
    output_path = Path(args.output) if args.output else Path(
        "benchmarks/results"
    ) / f"stage2-baseline-{captured_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    backend = LlamaCppCompletionBackend(config)
    records: list[dict[str, Any]] = []
    try:
        backend.start()
        for prompt in prompt_data["prompts"]:
            for iteration in range(1, args.runs_per_prompt + 1):
                request = InferenceRequest(
                    task_id=f"{prompt['id']}-{iteration}",
                    prompt=prompt["prompt"],
                    model_id=config.model_id,
                    max_generated_tokens=int(prompt["max_generated_tokens"]),
                )
                result = backend.generate(request)
                records.append(
                    {
                        "prompt_id": prompt["id"],
                        "category": prompt["category"],
                        "iteration": iteration,
                        "prompt": prompt["prompt"],
                        "output": result.text,
                        "metrics": result.metrics.as_dict() if result.metrics else {},
                    }
                )
                metrics = records[-1]["metrics"]
                print(
                    f"{prompt['id']}#{iteration}: "
                    f"TTFT={metrics.get('ttft_ms')} ms, "
                    f"generation={metrics.get('tokens_per_second')} tok/s"
                )
    finally:
        backend.shutdown()

    payload = {
        "schema_version": 1,
        "captured_at_utc": captured_at.isoformat(),
        "git_commit": _command_output(["git", "rev-parse", "HEAD"]),
        "git_worktree_clean": _command_output(["git", "status", "--porcelain"]) == "",
        "environment": {
            "platform": platform.platform(),
            "python": sys.version,
            "gpu": _command_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total",
                    "--format=csv,noheader",
                ]
            ),
        },
        "backend": {
            "name": backend.name,
            "version": backend.version,
            "release": config.release,
            "commit": config.commit,
        },
        "model": {
            "id": config.model_id,
            "revision": config.model_revision,
            "sha256": config.model_sha256,
            "file_bytes": config.model_path.stat().st_size,
        },
        "configuration": {
            "context_size": config.context_size,
            "batch_size": config.batch_size,
            "threads": config.threads,
            "gpu_layers": config.gpu_layers,
            "flash_attention": config.flash_attention,
            "temperature": config.temperature,
            "seed": config.seed,
            "resource_sample_interval_ms": config.resource_sample_interval_ms,
        },
        "measurement_notes": [
            "Each request launches a new llama-completion process and reloads the model.",
            "TTFT is process launch to first stdout byte and includes model load plus prompt evaluation.",
            "model_load_ms is parsed from llama.cpp log-clock markers around model loading.",
            "VRAM is a coarse 200 ms nvidia-smi total-device sample; unrelated GPU activity can affect it.",
            "peak_process_ram_mib is the llama-completion process peak working set, not total system RAM delta.",
            "generated_token_runs is llama.cpp eval runs and may differ from user-visible token count.",
            "Five samples are a baseline, not a statistically strong performance claim.",
            "git_commit identifies HEAD; git_worktree_clean records whether uncommitted source/config changes were present.",
        ],
        "records": records,
        "summary": _summarize(records),
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
