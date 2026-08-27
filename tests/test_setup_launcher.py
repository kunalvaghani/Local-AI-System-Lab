from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SetupLauncherTests(unittest.TestCase):
    def test_frontend_release_marker_matches_package_identity(self) -> None:
        marker = json.loads((ROOT / "apps/web/public/local-ai-release.json").read_text(encoding="utf-8"))
        package = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8"))
        self.assertEqual(marker, {
            "schema_version": 1,
            "product": "local-ai-systems-lab",
            "stage": 27,
            "version": package["version"],
        })

    def test_launcher_starts_related_services_before_frontend(self) -> None:
        launcher = (ROOT / "setup_and_run.bat").read_text(encoding="utf-8")
        optional_ollama = launcher.index("call :start_optional_ollama")
        backend = launcher.index("call :start_backend")
        frontend = launcher.index("call :start_frontend")
        self.assertLess(optional_ollama, backend)
        self.assertLess(backend, frontend)
        self.assertIn("[BACKEND] Starting first and waiting for health", launcher)

    def test_launcher_rejects_stale_backend_and_frontend_contracts(self) -> None:
        launcher = (ROOT / "setup_and_run.bat").read_text(encoding="utf-8")
        self.assertIn("call :check_backend_contract", launcher)
        self.assertIn("call :check_frontend_release", launcher)
        self.assertIn("/v1/tools", launcher)
        self.assertIn("/local-ai-release.json", launcher)
        self.assertIn("data/stage27-dev.db", launcher)
        self.assertIn("call npm.cmd ci", launcher)
        self.assertIn("call npm.cmd ls --depth=0", launcher)
        self.assertIn("npm ci cannot safely replace its native dependencies", launcher)
        self.assertIn("exit /b 1", launcher)


if __name__ == "__main__":
    unittest.main()
