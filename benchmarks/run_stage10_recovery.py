"""Run and retain the Stage 10 process-interruption recovery evidence."""

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
        [sys.executable, "-m", "runtime.recovery_cli"],
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
    path = output_dir / f"stage10-recovery-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": str(path), "final_state": payload["restart"]["final_state"], "integrity_check": payload["database_evidence"]["integrity_check"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
