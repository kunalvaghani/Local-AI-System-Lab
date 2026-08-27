from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.run_stage26_product_acceptance import (
    evaluate_product_acceptance,
    load_product_acceptance_config,
)
from runtime.errors import ConfigurationError


class ProductAcceptanceConfigTests(unittest.TestCase):
    def test_tracked_policy_is_strict_and_complete(self) -> None:
        config = load_product_acceptance_config()
        self.assertGreaterEqual(config.minimum_backend_tests, 151)
        self.assertGreaterEqual(config.minimum_frontend_tests, 39)
        self.assertIn("/runtime", config.required_browser_routes)
        self.assertEqual(config.required_failure_statuses["denied_tool"], 403)

    def test_unknown_policy_field_is_rejected(self) -> None:
        payload = json.loads(Path("configs/product-acceptance.json").read_text(encoding="utf-8"))
        payload["unexpected"] = True
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "product.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_product_acceptance_config(path)


class ProductAcceptanceClassificationTests(unittest.TestCase):
    def test_complete_local_evidence_is_release_candidate_with_honest_partials(self) -> None:
        config = load_product_acceptance_config()
        evidence = {
            "backend_gate": {"release_candidate": True, "tests": 152, "real_llm_calls": 1},
            "frontend_gate": {"tests": 39, "build_passed": True, "bundle_gzip_bytes": 151_000},
            "browser": {
                "routes_verified": list(config.required_browser_routes),
                "accessibility_violations": 0,
                "error_overlay_count": 0,
                "offline_state_verified": True,
                "elapsed_ms": 50_000,
            },
            "product_flow": {
                "inference_completed": True,
                "scheduler_reported": True,
                "route_reported": True,
                "model_reported": True,
                "tool_completed": True,
                "tool_trace_reported": True,
                "tool_telemetry_reported": True,
                "tool_duration_ms": 5,
            },
            "failure_paths": dict(config.required_failure_statuses),
            "restart": {
                "integrity": "ok",
                "inference_output_type": "inference",
                "tool_output_type": "tool",
                "browser_recovery_verified": True,
            },
        }
        result = evaluate_product_acceptance(config, evidence)
        self.assertTrue(result["release_candidate"])
        self.assertEqual(result["overall_classification"], "PARTIAL")
        self.assertEqual(result["subsystems"]["complete_local_product_flow"]["classification"], "DONE")
        self.assertEqual(result["subsystems"]["restart_and_recovery"]["classification"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
