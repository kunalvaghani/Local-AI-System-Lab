"""Run and retain the complete Stage 13 controlled chaos experiment."""

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
        [sys.executable, "-m", "runtime.chaos_cli", "--execute"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    payload = json.loads(completed.stdout)
    captured = datetime.now(timezone.utc)
    payload["retained_at_utc"] = captured.isoformat()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"stage13-chaos-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    summary = payload["summary"]
    print(
        json.dumps(
            {
                "output": str(path),
                "scenarios": summary["scenarios"],
                "injections": summary["injections"],
                "expected_outcome_rate_percent": summary["expected_outcome_rate_percent"],
                "containment_rate_percent": summary["containment_rate_percent"],
                "recovery_success_rate_percent": summary["recovery_success_rate_percent"],
                "database_integrity": payload["database_integrity"],
                "real_llm_calls": summary["real_llm_calls"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
