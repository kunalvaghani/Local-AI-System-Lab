"""Run and retain the Stage 11 trace, replay, and comparison evidence."""

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
        [sys.executable, "-m", "runtime.trace_cli", "demo"],
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
    path = output_dir / f"stage11-trace-replay-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "output": str(path),
        "runs": len(payload["runs"]),
        "trace_steps": [run["step_count"] for run in payload["runs"]],
        "replay_status": payload["replay"]["status"],
        "deterministic_matches": payload["comparison"]["deterministic_matches"],
        "deterministic_divergences": payload["comparison"]["deterministic_divergences"],
        "integrity_check": payload["integrity_check"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
