"""Validate the human and machine evidence required for the Stage 27 portfolio release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class PortfolioValidationError(ValueError):
    """Raised when the tracked release manifest is malformed."""


MANIFEST_FIELDS = {
    "schema_version",
    "stage",
    "release_label",
    "release_scope",
    "required_documents",
    "required_screenshots",
    "required_evidence",
    "required_readme_sections",
}
SCREENSHOT_FIELDS = {"path", "minimum_width", "minimum_height"}
EVIDENCE_FIELDS = {"path", "assertions"}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PortfolioValidationError(f"{name} must be a non-empty string")
    return value


def _string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PortfolioValidationError(f"{name} must be a non-empty list")
    resolved = [_nonempty_string(item, f"{name} item") for item in value]
    if len(set(resolved)) != len(resolved):
        raise PortfolioValidationError(f"{name} contains duplicate entries")
    return resolved


def load_manifest(path: str | Path = "configs/portfolio-release.json") -> dict[str, Any]:
    resolved = Path(path).resolve()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PortfolioValidationError(f"unable to read portfolio manifest: {resolved}") from error
    if not isinstance(payload, dict) or set(payload) != MANIFEST_FIELDS:
        raise PortfolioValidationError("portfolio manifest fields are invalid")
    if payload["schema_version"] != 1 or payload["stage"] != 27:
        raise PortfolioValidationError("portfolio manifest must declare schema 1 and stage 27")
    _nonempty_string(payload["release_label"], "release_label")
    _nonempty_string(payload["release_scope"], "release_scope")
    _string_list(payload["required_documents"], "required_documents")
    _string_list(payload["required_readme_sections"], "required_readme_sections")
    screenshots = payload["required_screenshots"]
    if not isinstance(screenshots, list) or not screenshots:
        raise PortfolioValidationError("required_screenshots must be a non-empty list")
    for item in screenshots:
        if not isinstance(item, dict) or set(item) != SCREENSHOT_FIELDS:
            raise PortfolioValidationError("screenshot manifest fields are invalid")
        _nonempty_string(item["path"], "screenshot path")
        for field in ("minimum_width", "minimum_height"):
            if isinstance(item[field], bool) or not isinstance(item[field], int) or item[field] <= 0:
                raise PortfolioValidationError(f"{field} must be a positive integer")
    evidence = payload["required_evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise PortfolioValidationError("required_evidence must be a non-empty list")
    for item in evidence:
        if not isinstance(item, dict) or set(item) != EVIDENCE_FIELDS:
            raise PortfolioValidationError("evidence manifest fields are invalid")
        _nonempty_string(item["path"], "evidence path")
        if not isinstance(item["assertions"], dict) or not item["assertions"]:
            raise PortfolioValidationError("evidence assertions must be a non-empty object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("not a PNG with an IHDR header")
    return struct.unpack(">II", header[16:24])


def _dotted(payload: Any, dotted: str) -> Any:
    value = payload
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(dotted)
        value = value[part]
    return value


def _local_link_target(document: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    path_text = target.split("#", 1)[0].replace("%20", " ")
    return (document.parent / path_text).resolve()


def validate_portfolio_release(
    manifest_path: str | Path = "configs/portfolio-release.json",
) -> dict[str, Any]:
    started = time.perf_counter()
    manifest_file = Path(manifest_path).resolve()
    root = manifest_file.parent.parent
    manifest = load_manifest(manifest_file)
    checks: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    documents: list[Path] = []
    links_checked = 0

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    for relative in manifest["required_documents"]:
        path = (root / relative).resolve()
        exists = path.is_file()
        record(f"document:{relative}", exists, "present" if exists else "missing")
        if exists:
            documents.append(path)
            artifacts.append({"path": relative, "sha256": _sha256(path), "bytes": path.stat().st_size})

    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for section in manifest["required_readme_sections"]:
        record(f"readme:{section}", section in readme_text, "heading present" if section in readme_text else "heading missing")

    for document in documents:
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = _local_link_target(document, raw_target)
            if target is None:
                continue
            links_checked += 1
            try:
                target.relative_to(root)
                contained = True
            except ValueError:
                contained = False
            exists = contained and target.exists()
            label = document.relative_to(root).as_posix()
            record(f"link:{label}:{raw_target}", exists, "resolved" if exists else "missing or outside repository")

    for item in manifest["required_screenshots"]:
        relative = item["path"]
        path = (root / relative).resolve()
        try:
            width, height = _png_dimensions(path)
            passed = width >= item["minimum_width"] and height >= item["minimum_height"]
            detail = f"{width}x{height}"
            artifacts.append({"path": relative, "sha256": _sha256(path), "bytes": path.stat().st_size, "width": width, "height": height})
        except (OSError, ValueError) as error:
            passed = False
            detail = type(error).__name__
        record(f"screenshot:{relative}", passed, detail)

    for item in manifest["required_evidence"]:
        relative = item["path"]
        path = (root / relative).resolve()
        try:
            evidence = json.loads(path.read_text(encoding="utf-8"))
            artifacts.append({"path": relative, "sha256": _sha256(path), "bytes": path.stat().st_size})
        except (OSError, json.JSONDecodeError) as error:
            record(f"evidence:{relative}", False, type(error).__name__)
            continue
        for dotted, expected in item["assertions"].items():
            try:
                actual = _dotted(evidence, dotted)
                passed = actual == expected
                detail = f"expected={expected!r}, actual={actual!r}"
            except KeyError:
                passed = False
                detail = "field missing"
            record(f"evidence:{relative}:{dotted}", passed, detail)

    failed = [check for check in checks if not check["passed"]]
    return {
        "schema_version": 1,
        "stage": 27,
        "release_label": manifest["release_label"],
        "release_scope": manifest["release_scope"],
        "run_id": str(uuid4()),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_ready": not failed,
        "summary": {
            "checks": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
            "documents": len(manifest["required_documents"]),
            "screenshots": len(manifest["required_screenshots"]),
            "evidence_files": len(manifest["required_evidence"]),
            "local_links_checked": links_checked,
            "validation_ms": round((time.perf_counter() - started) * 1000, 3),
        },
        "checks": checks,
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
    }


def _default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("benchmarks/results") / f"stage27-portfolio-release-{stamp}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="configs/portfolio-release.json")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result = validate_portfolio_release(args.manifest)
    except PortfolioValidationError as error:
        print(json.dumps({"code": "portfolio_manifest_invalid", "message": str(error)}))
        return 2
    output = (args.output or _default_output()).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "release_ready": result["release_ready"], **result["summary"]}, sort_keys=True))
    return 0 if result["release_ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
