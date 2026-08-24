"""Run and retain the Stage 12 unified observability demonstration."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="benchmarks/results")
    args = parser.parse_args()
    completed = subprocess.run(
        [sys.executable, "-m", "runtime.observability_cli", "demo"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(completed.stdout)
    captured = datetime.now(timezone.utc)
    payload["retained_at_utc"] = captured.isoformat()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"stage12-observability-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    report = payload["report"]
    print(
        json.dumps(
            {
                "output": str(path),
                "tasks": report["totals"]["tasks"],
                "model_calls": report["totals"]["model_calls_started"],
                "tool_calls": report["totals"]["tool_calls"],
                "failures": report["totals"]["failed_tasks"],
                "recoveries": report["totals"]["recoveries"],
                "recent_tasks": len(report["recent_tasks"]),
                "live_hardware": report["live"]["hardware"] is not None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
