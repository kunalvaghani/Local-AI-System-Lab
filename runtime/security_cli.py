"""Run the repeatable Stage 14 adversarial security suite."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from .errors import LabError
from .security.runner import CASE_IDS, run_security_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 14 deterministic adversarial security tests.",
    )
    parser.add_argument("--case", action="append", choices=CASE_IDS, dest="cases")
    parser.add_argument("--security-config", default="configs/security.json")
    parser.add_argument("--database")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database = (
        Path(args.database).resolve()
        if args.database
        else (Path("data") / f"stage14-security-{uuid4().hex}.db").resolve()
    )
    try:
        report = run_security_suite(
            database,
            selected=tuple(args.cases) if args.cases else None,
            security_config_path=args.security_config,
        )
    except LabError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 1
    payload = report.as_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["summary"]["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
