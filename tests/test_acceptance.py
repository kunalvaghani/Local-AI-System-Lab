from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from benchmarks.run_stage16_acceptance import (
    CLASSIFICATIONS,
    classify_acceptance,
    load_acceptance_config,
)
from runtime.errors import ConfigurationError


class AcceptanceConfigTests(unittest.TestCase):
    def test_tracked_config_is_strict_and_references_real_baseline(self) -> None:
        config = load_acceptance_config()
        self.assertGreaterEqual(config.minimum_test_count, 150)
        self.assertTrue(config.stage2_baseline_result.is_file())
        with self.assertRaises(ConfigurationError):
            replace(config, minimum_test_count=0)  # dataclass replacement alone is intentionally not a loader

    def test_loader_rejects_unknown_fields(self) -> None:
        source = json.loads(Path("configs/acceptance.json").read_text(encoding="utf-8"))
        source["unexpected"] = True
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "acceptance.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_acceptance_config(path)


class AcceptanceClassificationTests(unittest.TestCase):
    def test_complete_evidence_is_release_candidate_with_honest_partial_classifications(self) -> None:
        config = load_acceptance_config()
        summaries = {
            "full_tests": {"tests": config.minimum_test_count},
            "scheduler": {"matches_expected": True},
            "hardware": {"controlled_policy_demonstration": {
                value: {} for value in ("ACCEPT", "QUEUE", "REDUCE_CONTEXT", "REDUCE_GPU_OFFLOAD", "FALLBACK", "REJECT_UNSAFE")
            }},
            "recovery": {"restart": {"final_state": "completed"}, "database_evidence": {"integrity_check": "ok"}},
            "trace": {"integrity_check": "ok", "replay": {"integrity_valid": True}},
            "observability": {"report": {"totals": {"tasks": 4}}},
            "chaos": {"summary": {"scenarios": 9, "expected_outcome_rate_percent": 100.0, "recovery_success_rate_percent": 100.0}},
            "security": {"summary": {"cases": 14, "failed": 0, "integrity_check": "ok"}},
            "api_stub": {"passed": True, "process_boundary": {"real_llm_calls": 0}, "evidence": {"database_integrity": "ok"}},
            "api_real": {
                "passed": True,
                "process_boundary": {"real_llm_calls": 1},
                "operations": {"task_events": {"duration_ms": 5_000}},
                "evidence": {"database_integrity": "ok", "inference_metrics": {
                    "tokens_per_second": 100.0,
                    "ttft_ms": 2_000.0,
                    "peak_process_ram_mib": 1_400.0,
                    "vram_delta_mib": 1_200.0,
                }},
            },
        }
        commands = {
            "compile": {"passed": True},
            "package": {"passed": True},
            "control_tests": {"passed": True},
            "fault_tests": {"passed": True},
        }
        result = classify_acceptance(config, summaries, commands)
        self.assertTrue(result["release_candidate"])
        self.assertEqual(result["overall_classification"], "PARTIAL")
        self.assertEqual(result["subsystems"]["backend_api"]["classification"], "DONE")
        self.assertEqual(result["subsystems"]["persistence_and_recovery"]["classification"], "PARTIAL")
        self.assertTrue(all(item["classification"] in CLASSIFICATIONS for item in result["subsystems"].values()))


if __name__ == "__main__":
    unittest.main()
