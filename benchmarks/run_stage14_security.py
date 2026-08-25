"""Run and retain the complete Stage 14 adversarial security report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from runtime.security.runner import run_security_suite


def main() -> int:
    captured = datetime.now(timezone.utc)
    database = (Path("data") / f"stage14-security-{uuid4().hex}.db").resolve()
    report = run_security_suite(database).as_dict()
    output_dir = Path("benchmarks/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"stage14-security-{captured.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(path.resolve()), "summary": report["summary"]}, indent=2, sort_keys=True))
    return 0 if report["summary"]["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
