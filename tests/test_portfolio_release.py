from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from scripts.validate_portfolio_release import (
    PortfolioValidationError,
    load_manifest,
    validate_portfolio_release,
)


def png_header(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height)


class PortfolioReleaseTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        (root / "configs").mkdir()
        (root / "docs").mkdir()
        (root / "assets").mkdir()
        (root / "README.md").write_text("# Project\n\n## Required\n\n[Guide](docs/guide.md)\n", encoding="utf-8")
        (root / "docs" / "guide.md").write_text("# Guide\n\n[Evidence](../evidence.json)\n", encoding="utf-8")
        (root / "assets" / "shot.png").write_bytes(png_header(1200, 700))
        (root / "evidence.json").write_text(json.dumps({"release": {"ready": True}}), encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "stage": 27,
            "release_label": "test",
            "release_scope": "test scope",
            "required_documents": ["README.md", "docs/guide.md"],
            "required_screenshots": [{"path": "assets/shot.png", "minimum_width": 1200, "minimum_height": 700}],
            "required_evidence": [{"path": "evidence.json", "assertions": {"release.ready": True}}],
            "required_readme_sections": ["## Required"],
        }
        path = root / "configs" / "portfolio-release.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_complete_release_passes_with_links_screenshot_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            result = validate_portfolio_release(self.fixture(Path(name)))
        self.assertTrue(result["release_ready"])
        self.assertEqual(result["summary"]["failed"], 0)
        self.assertEqual(result["summary"]["local_links_checked"], 2)

    def test_broken_local_link_fails_release(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            manifest = self.fixture(root)
            (root / "docs" / "guide.md").write_text("[Missing](missing.md)\n", encoding="utf-8")
            result = validate_portfolio_release(manifest)
        self.assertFalse(result["release_ready"])
        self.assertTrue(any(not check["passed"] and check["name"].startswith("link:") for check in result["checks"]))

    def test_unknown_manifest_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            path = self.fixture(Path(name))
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["unexpected"] = True
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(PortfolioValidationError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
