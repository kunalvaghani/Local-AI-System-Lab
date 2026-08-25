"""Run and classify the complete Stage 16 backend acceptance gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Sequence
from uuid import uuid4

from runtime.errors import ConfigurationError


CLASSIFICATIONS = {"DONE", "PARTIAL", "FAILED", "DEFERRED"}


@dataclass(frozen=True, slots=True)
class AcceptanceConfig:
    release_scope: str
    minimum_test_count: int
    expected_security_cases: int
    expected_chaos_scenarios: int
    minimum_expected_chaos_rate_percent: float
    minimum_recovery_success_rate_percent: float
    minimum_real_tokens_per_second: float
    maximum_real_ttft_regression_percent: float
    maximum_real_peak_ram_mib: float
    maximum_real_vram_delta_mib: float
    maximum_real_api_stream_ms: float
    stage2_baseline_result: Path

    def __post_init__(self) -> None:
        if not self.release_scope.strip():
            raise ConfigurationError("backend acceptance release_scope must be non-empty")
        for name in ("minimum_test_count", "expected_security_cases", "expected_chaos_scenarios"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ConfigurationError(f"backend acceptance {name} must be a positive integer")
        for name in (
            "minimum_expected_chaos_rate_percent", "minimum_recovery_success_rate_percent",
            "minimum_real_tokens_per_second", "maximum_real_ttft_regression_percent",
            "maximum_real_peak_ram_mib", "maximum_real_vram_delta_mib",
            "maximum_real_api_stream_ms",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0:
                raise ConfigurationError(f"backend acceptance {name} must be a positive number")
        if not self.stage2_baseline_result.is_file():
            raise ConfigurationError(
                "backend acceptance baseline result is missing",
                details={"path": str(self.stage2_baseline_result)},
            )


def load_acceptance_config(path: str | Path = "configs/acceptance.json") -> AcceptanceConfig:
    resolved = Path(path).resolve()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "failed to read backend acceptance configuration",
            details={"path": str(resolved), "cause_type": type(error).__name__},
        ) from error
    expected = {
        "schema_version", "release_scope", "minimum_test_count",
        "expected_security_cases", "expected_chaos_scenarios",
        "minimum_expected_chaos_rate_percent",
        "minimum_recovery_success_rate_percent", "minimum_real_tokens_per_second",
        "maximum_real_ttft_regression_percent", "maximum_real_peak_ram_mib",
        "maximum_real_vram_delta_mib", "maximum_real_api_stream_ms",
        "stage2_baseline_result",
    }
    if not isinstance(payload, dict) or set(payload) != expected or payload.get("schema_version") != 1:
        raise ConfigurationError("backend acceptance configuration schema or fields are invalid")
    if not isinstance(payload["release_scope"], str) or not payload["release_scope"].strip():
        raise ConfigurationError("backend acceptance release_scope must be non-empty")
    integer_names = ("minimum_test_count", "expected_security_cases", "expected_chaos_scenarios")
    for name in integer_names:
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigurationError(f"backend acceptance {name} must be a positive integer")
    number_names = (
        "minimum_expected_chaos_rate_percent", "minimum_recovery_success_rate_percent",
        "minimum_real_tokens_per_second", "maximum_real_ttft_regression_percent",
        "maximum_real_peak_ram_mib", "maximum_real_vram_delta_mib",
        "maximum_real_api_stream_ms",
    )
    for name in number_names:
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0:
            raise ConfigurationError(f"backend acceptance {name} must be a positive number")
    root = resolved.parent.parent
    baseline = (root / str(payload["stage2_baseline_result"])).resolve()
    if not baseline.is_file():
        raise ConfigurationError(
            "backend acceptance baseline result is missing",
            details={"path": str(baseline)},
        )
    return AcceptanceConfig(
        release_scope=payload["release_scope"],
        minimum_test_count=payload["minimum_test_count"],
        expected_security_cases=payload["expected_security_cases"],
        expected_chaos_scenarios=payload["expected_chaos_scenarios"],
        minimum_expected_chaos_rate_percent=float(payload["minimum_expected_chaos_rate_percent"]),
        minimum_recovery_success_rate_percent=float(payload["minimum_recovery_success_rate_percent"]),
        minimum_real_tokens_per_second=float(payload["minimum_real_tokens_per_second"]),
        maximum_real_ttft_regression_percent=float(payload["maximum_real_ttft_regression_percent"]),
        maximum_real_peak_ram_mib=float(payload["maximum_real_peak_ram_mib"]),
        maximum_real_vram_delta_mib=float(payload["maximum_real_vram_delta_mib"]),
        maximum_real_api_stream_ms=float(payload["maximum_real_api_stream_ms"]),
        stage2_baseline_result=baseline,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _json(value: str) -> dict[str, Any]:
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("command JSON output must be an object")
    return payload


def _git(command: Sequence[str]) -> str:
    result = subprocess.run(
        list(command), cwd=Path.cwd(), capture_output=True, text=True, timeout=20, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _command(
    name: str,
    arguments: Sequence[str],
    *,
    timeout_seconds: float = 180.0,
    summarize: Callable[[str, str], dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    started = perf_counter()
    timed_out = False
    try:
        result = subprocess.run(
            list(arguments),
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = -1
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
    duration_ms = (perf_counter() - started) * 1000.0
    summary: dict[str, Any] | None = None
    summary_error: str | None = None
    if exit_code == 0 and summarize is not None:
        try:
            summary = summarize(stdout, stderr)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            summary_error = f"{type(error).__name__}: {error}"
    record = {
        "name": name,
        "command": subprocess.list2cmdline(list(arguments)),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "timed_out": timed_out,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "summary_parsed": summary is not None if summarize is not None else True,
        "summary_error": summary_error,
        "passed": exit_code == 0 and not timed_out and summary_error is None,
    }
    return record, summary


def _test_summary(stdout: str, stderr: str) -> dict[str, Any]:
    combined = stdout + "\n" + stderr
    match = re.search(r"Ran\s+(\d+)\s+tests?\s+in\s+([0-9.]+)s", combined)
    if not match or not re.search(r"\nOK\s*$", combined.strip() + "\n"):
        raise ValueError("unittest completion summary was not found")
    return {"tests": int(match.group(1)), "reported_duration_seconds": float(match.group(2))}


def _baseline(path: Path) -> dict[str, float]:
    payload = _json(path.read_text(encoding="utf-8"))
    metrics = [record["metrics"] for record in payload["records"]]
    return {
        "ttft_ms_median": statistics.median(float(item["ttft_ms"]) for item in metrics),
        "tokens_per_second_median": statistics.median(float(item["tokens_per_second"]) for item in metrics),
        "peak_process_ram_mib_median": statistics.median(float(item["peak_process_ram_mib"]) for item in metrics),
        "vram_delta_mib_median": statistics.median(float(item["vram_delta_mib"]) for item in metrics),
    }


def _item(
    classification: str,
    evidence: list[str],
    rationale: str,
) -> dict[str, Any]:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unsupported classification: {classification}")
    return {"classification": classification, "evidence": evidence, "rationale": rationale}


def classify_acceptance(
    config: AcceptanceConfig,
    summaries: dict[str, dict[str, Any]],
    command_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tests = summaries.get("full_tests", {})
    scheduler = summaries.get("scheduler", {})
    hardware = summaries.get("hardware", {})
    recovery = summaries.get("recovery", {})
    trace = summaries.get("trace", {})
    observability = summaries.get("observability", {})
    chaos = summaries.get("chaos", {})
    security = summaries.get("security", {})
    api_stub = summaries.get("api_stub", {})
    api_real = summaries.get("api_real", {})
    baseline = _baseline(config.stage2_baseline_result)
    real_metrics = api_real.get("evidence", {}).get("inference_metrics") or {}
    current_ttft = float(real_metrics.get("ttft_ms", float("inf")))
    ttft_regression = (
        (current_ttft - baseline["ttft_ms_median"]) / baseline["ttft_ms_median"] * 100.0
    )
    benchmark_checks = {
        "tokens_per_second": {
            "actual": real_metrics.get("tokens_per_second"),
            "minimum": config.minimum_real_tokens_per_second,
            "passed": float(real_metrics.get("tokens_per_second", 0)) >= config.minimum_real_tokens_per_second,
        },
        "ttft_regression_percent": {
            "actual": ttft_regression,
            "maximum": config.maximum_real_ttft_regression_percent,
            "baseline_ttft_ms": baseline["ttft_ms_median"],
            "current_ttft_ms": real_metrics.get("ttft_ms"),
            "passed": ttft_regression <= config.maximum_real_ttft_regression_percent,
        },
        "peak_process_ram_mib": {
            "actual": real_metrics.get("peak_process_ram_mib"),
            "maximum": config.maximum_real_peak_ram_mib,
            "passed": float(real_metrics.get("peak_process_ram_mib", float("inf"))) <= config.maximum_real_peak_ram_mib,
        },
        "vram_delta_mib": {
            "actual": real_metrics.get("vram_delta_mib"),
            "maximum": config.maximum_real_vram_delta_mib,
            "passed": float(real_metrics.get("vram_delta_mib", float("inf"))) <= config.maximum_real_vram_delta_mib,
        },
        "api_stream_ms": {
            "actual": api_real.get("operations", {}).get("task_events", {}).get("duration_ms"),
            "maximum": config.maximum_real_api_stream_ms,
            "passed": float(api_real.get("operations", {}).get("task_events", {}).get("duration_ms", float("inf"))) <= config.maximum_real_api_stream_ms,
        },
    }
    required = {
        "build_and_package": (
            command_records.get("compile", {}).get("passed", False)
            and command_records.get("package", {}).get("passed", False)
        ),
        "unit_and_integration_tests": int(tests.get("tests", 0)) >= config.minimum_test_count,
        "edge_cases_cancellation_timeouts": command_records.get("control_tests", {}).get("passed", False),
        "malformed_model_output": command_records.get("fault_tests", {}).get("passed", False),
        "scheduler_behavior": bool(scheduler.get("matches_expected")),
        "persistence_restart_recovery": (
            recovery.get("restart", {}).get("final_state") == "completed"
            and recovery.get("database_evidence", {}).get("integrity_check") == "ok"
        ),
        "resource_pressure": set(hardware.get("controlled_policy_demonstration", {})) == {
            "ACCEPT", "QUEUE", "REDUCE_CONTEXT", "REDUCE_GPU_OFFLOAD", "FALLBACK", "REJECT_UNSAFE"
        },
        "trace_and_replay": (
            trace.get("integrity_check") == "ok"
            and trace.get("replay", {}).get("integrity_valid") is True
        ),
        "observability": observability.get("report", {}).get("totals", {}).get("tasks", 0) >= 4,
        "fault_injection": (
            chaos.get("summary", {}).get("scenarios") == config.expected_chaos_scenarios
            and chaos.get("summary", {}).get("expected_outcome_rate_percent") >= config.minimum_expected_chaos_rate_percent
            and chaos.get("summary", {}).get("recovery_success_rate_percent") >= config.minimum_recovery_success_rate_percent
        ),
        "security": (
            security.get("summary", {}).get("cases") == config.expected_security_cases
            and security.get("summary", {}).get("failed") == 0
            and security.get("summary", {}).get("integrity_check") == "ok"
        ),
        "api_deterministic": (
            api_stub.get("passed") is True
            and api_stub.get("process_boundary", {}).get("real_llm_calls") == 0
            and api_stub.get("evidence", {}).get("database_integrity") == "ok"
        ),
        "api_real_model": (
            api_real.get("passed") is True
            and api_real.get("process_boundary", {}).get("real_llm_calls") == 1
            and api_real.get("evidence", {}).get("database_integrity") == "ok"
        ),
        "benchmark_regression": all(item["passed"] for item in benchmark_checks.values()),
    }
    subsystems = {
        "core_runtime": _item(
            "DONE" if required["build_and_package"] and required["unit_and_integration_tests"] else "FAILED",
            ["compile", "package", "full_tests", "control_tests"],
            "Complete suite and targeted cancellation/timeout controls meet the tracked minimum.",
        ),
        "scheduler_and_resource_admission": _item(
            "DONE" if required["scheduler_behavior"] and required["resource_pressure"] else "FAILED",
            ["scheduler", "hardware"],
            "FIFO/priority order and all six controlled admission outcomes are demonstrated.",
        ),
        "persistence_and_recovery": _item(
            "PARTIAL" if required["persistence_restart_recovery"] else "FAILED",
            ["recovery", "chaos"],
            "Killed-process pre-invocation recovery succeeds, but the known terminal-state/output atomicity gap remains.",
        ),
        "tracing_replay_observability": _item(
            "DONE" if required["trace_and_replay"] and required["observability"] else "FAILED",
            ["trace", "observability"],
            "Trace integrity/replay and unified durable/live telemetry meet the current local scope.",
        ),
        "fault_injection": _item(
            "PARTIAL" if required["fault_injection"] else "FAILED",
            ["chaos"],
            "All expected outcomes and recovery pass; containment remains 8/9 because the atomicity gap is deliberately reproduced.",
        ),
        "security": _item(
            "PARTIAL" if required["security"] else "FAILED",
            ["security"],
            "All bounded adversarial cases pass, but controls are application-level and are not an OS sandbox or certification.",
        ),
        "backend_api": _item(
            "DONE" if required["api_deterministic"] and required["api_real_model"] else "FAILED",
            ["api_stub", "api_real"],
            "Separate-process deterministic and real-model HTTP/SSE workflows pass the loopback contract.",
        ),
        "model_routing_and_evaluation": _item(
            "PARTIAL",
            ["full_tests", "api_real"],
            "Routing is explainable, but only one real model backend exists and semantic output evaluation remains deferred.",
        ),
        "remote_multi_user_deployment": _item(
            "DEFERRED",
            [],
            "TLS, authentication, identity authorization, remote serving, and production HTTP infrastructure are outside the approved local scope.",
        ),
    }
    failed_subsystems = [name for name, item in subsystems.items() if item["classification"] == "FAILED"]
    all_required_passed = all(required.values()) and not failed_subsystems
    return {
        "required_categories": {
            name: {"status": "PASS" if passed else "FAIL"}
            for name, passed in required.items()
        },
        "benchmark_baseline": baseline,
        "benchmark_checks": benchmark_checks,
        "subsystems": subsystems,
        "overall_classification": "PARTIAL" if all_required_passed else "FAILED",
        "release_candidate": all_required_passed,
        "gate_recommendation": (
            "ACCEPT_FOR_SINGLE_USER_LOOPBACK_FRONTEND_WITH_TRACKED_LIMITATIONS"
            if all_required_passed
            else "REJECT_UNTIL_FAILED_REQUIRED_CATEGORIES_ARE_FIXED"
        ),
        "frontend_authorization": "PENDING_EXPLICIT_USER_APPROVAL",
    }


def run_acceptance(
    config_path: str | Path = "configs/acceptance.json",
    output: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = load_acceptance_config(config_path)
    python = sys.executable
    started_at = datetime.now(timezone.utc)
    records: list[dict[str, Any]] = []
    summaries: dict[str, dict[str, Any]] = {}

    def run(
        name: str,
        args: Sequence[str],
        *,
        timeout: float = 180.0,
        parser: Callable[[str, str], dict[str, Any]] | None = None,
    ) -> None:
        record, summary = _command(name, args, timeout_seconds=timeout, summarize=parser)
        records.append(record)
        if summary is not None:
            summaries[name] = summary

    with tempfile.TemporaryDirectory(prefix="stage16-", dir=Path("data")) as temporary:
        temp = Path(temporary)
        api_stub_path = temp / "api-stub.json"
        api_real_path = temp / "api-real.json"
        run("compile", [python, "-m", "compileall", "-q", "runtime", "tests", "benchmarks"])
        run("package", [python, "-m", "pip", "install", "--dry-run", "--no-deps", "--no-build-isolation", "."])
        run("full_tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout=240, parser=_test_summary)
        run(
            "control_tests",
            [python, "-m", "unittest", "tests.test_api.Stage15CancellationApiTests", "tests.test_scheduler.SchedulerControlTests", "-v"],
            parser=_test_summary,
        )
        run(
            "fault_tests",
            [python, "-m", "unittest", "tests.test_fault_injection.FaultAdapterTests", "-v"],
            parser=_test_summary,
        )
        run("scheduler", [python, "-m", "runtime.scheduler_cli"], parser=lambda out, err: _json(out))
        run("hardware", [python, "-m", "runtime.hardware_cli"], parser=lambda out, err: _json(out))
        run("recovery", [python, "-m", "runtime.recovery_cli", "--db", str(temp / "recovery.db")], parser=lambda out, err: _json(out))
        run("trace", [python, "-m", "runtime.trace_cli", "demo", "--database", str(temp / "trace.db")], parser=lambda out, err: _json(out))
        run("observability", [python, "-m", "runtime.observability_cli", "demo", "--database", str(temp / "observability.db")], parser=lambda out, err: _json(out))
        run("chaos", [python, "-m", "runtime.chaos_cli", "--execute", "--database", str(temp / "chaos.db")], timeout=240, parser=lambda out, err: _json(out))
        run("security", [python, "-m", "runtime.security_cli", "--database", str(temp / "security.db")], parser=lambda out, err: _json(out))
        run("api_stub", [python, "-m", "benchmarks.run_stage15_api", "--output", str(api_stub_path)], timeout=180)
        if api_stub_path.is_file():
            summaries["api_stub"] = _json(api_stub_path.read_text(encoding="utf-8"))
        run("api_real", [python, "-m", "benchmarks.run_stage15_api", "--real", "--output", str(api_real_path)], timeout=240)
        if api_real_path.is_file():
            summaries["api_real"] = _json(api_real_path.read_text(encoding="utf-8"))

        by_name = {record["name"]: record for record in records}
        evaluation = classify_acceptance(config, summaries, by_name)

    payload = {
        "schema_version": 1,
        "stage": 16,
        "run_id": str(uuid4()),
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_scope": config.release_scope,
        "acceptance_policy": {
            "minimum_test_count": config.minimum_test_count,
            "expected_security_cases": config.expected_security_cases,
            "expected_chaos_scenarios": config.expected_chaos_scenarios,
            "minimum_expected_chaos_rate_percent": config.minimum_expected_chaos_rate_percent,
            "minimum_recovery_success_rate_percent": config.minimum_recovery_success_rate_percent,
            "minimum_real_tokens_per_second": config.minimum_real_tokens_per_second,
            "maximum_real_ttft_regression_percent": config.maximum_real_ttft_regression_percent,
            "maximum_real_peak_ram_mib": config.maximum_real_peak_ram_mib,
            "maximum_real_vram_delta_mib": config.maximum_real_vram_delta_mib,
            "maximum_real_api_stream_ms": config.maximum_real_api_stream_ms,
            "stage2_baseline_result": str(config.stage2_baseline_result),
        },
        "environment": {
            "python": sys.version,
            "git_head": _git(["git", "rev-parse", "HEAD"]),
            "git_status_entries": len(_git(["git", "status", "--short"]).splitlines()),
        },
        "commands": records,
        "summaries": {
            "full_tests": summaries.get("full_tests"),
            "control_tests": summaries.get("control_tests"),
            "fault_tests": summaries.get("fault_tests"),
            "scheduler": {
                "matches_expected": summaries.get("scheduler", {}).get("matches_expected"),
                "fifo_order": summaries.get("scheduler", {}).get("comparison", {}).get("fifo", {}).get("controlled_execution_order"),
                "priority_order": summaries.get("scheduler", {}).get("comparison", {}).get("priority", {}).get("controlled_execution_order"),
            },
            "hardware": {
                "live_action": summaries.get("hardware", {}).get("live_admission", {}).get("action"),
                "controlled_actions": sorted(summaries.get("hardware", {}).get("controlled_policy_demonstration", {})),
                "warnings": summaries.get("hardware", {}).get("hardware", {}).get("warnings", []),
            },
            "recovery": {
                "final_state": summaries.get("recovery", {}).get("restart", {}).get("final_state"),
                "integrity": summaries.get("recovery", {}).get("database_evidence", {}).get("integrity_check"),
                "real_llm_calls": summaries.get("recovery", {}).get("restart", {}).get("real_llm_calls"),
            },
            "trace": {
                "integrity": summaries.get("trace", {}).get("integrity_check"),
                "replay_status": summaries.get("trace", {}).get("replay", {}).get("status"),
                "replay_integrity_valid": summaries.get("trace", {}).get("replay", {}).get("integrity_valid"),
                "deterministic_divergences": summaries.get("trace", {}).get("comparison", {}).get("deterministic_divergences"),
            },
            "observability": {
                "tasks": summaries.get("observability", {}).get("report", {}).get("totals", {}).get("tasks"),
                "recoveries": summaries.get("observability", {}).get("report", {}).get("totals", {}).get("recoveries"),
                "trace_steps": summaries.get("observability", {}).get("report", {}).get("totals", {}).get("trace_steps"),
            },
            "chaos": summaries.get("chaos", {}).get("summary"),
            "security": summaries.get("security", {}).get("summary"),
            "api_stub": {
                "passed": summaries.get("api_stub", {}).get("passed"),
                "operations": len(summaries.get("api_stub", {}).get("operations", {})),
                "real_llm_calls": summaries.get("api_stub", {}).get("process_boundary", {}).get("real_llm_calls"),
                "database_integrity": summaries.get("api_stub", {}).get("evidence", {}).get("database_integrity"),
            },
            "api_real": {
                "passed": summaries.get("api_real", {}).get("passed"),
                "operations": len(summaries.get("api_real", {}).get("operations", {})),
                "real_llm_calls": summaries.get("api_real", {}).get("process_boundary", {}).get("real_llm_calls"),
                "model_id": summaries.get("api_real", {}).get("evidence", {}).get("model_id"),
                "selected_profile": (summaries.get("api_real", {}).get("evidence", {}).get("selected_profile") or {}).get("profile_id"),
                "inference_metrics": summaries.get("api_real", {}).get("evidence", {}).get("inference_metrics"),
                "database_integrity": summaries.get("api_real", {}).get("evidence", {}).get("database_integrity"),
            },
        },
        "evaluation": evaluation,
    }
    resolved_output = output or (
        Path("benchmarks/results")
        / f"stage16-backend-acceptance-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved_output.resolve(), payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/acceptance.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        output, payload = run_acceptance(args.config, args.output)
    except (ConfigurationError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        details = error.as_dict() if isinstance(error, ConfigurationError) else {
            "code": "backend_acceptance_failed",
            "message": str(error),
        }
        print(json.dumps(details, sort_keys=True), file=sys.stderr)
        return 2
    evaluation = payload["evaluation"]
    print(json.dumps({
        "output": str(output),
        "overall_classification": evaluation["overall_classification"],
        "release_candidate": evaluation["release_candidate"],
        "gate_recommendation": evaluation["gate_recommendation"],
    }, sort_keys=True))
    return 0 if evaluation["release_candidate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
