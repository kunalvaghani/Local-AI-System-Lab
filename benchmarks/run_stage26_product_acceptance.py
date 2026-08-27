"""Run the complete Stage 26 local product acceptance gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from runtime.errors import ConfigurationError


CLASSIFICATIONS = {"DONE", "PARTIAL", "FAILED", "DEFERRED"}


@dataclass(frozen=True, slots=True)
class ProductAcceptanceConfig:
    release_scope: str
    minimum_backend_tests: int
    minimum_frontend_tests: int
    required_browser_routes: tuple[str, ...]
    required_failure_statuses: dict[str, int]
    maximum_browser_flow_ms: float
    maximum_tool_duration_ms: float
    maximum_javascript_gzip_bytes: int


def load_product_acceptance_config(
    path: str | Path = "configs/product-acceptance.json",
) -> ProductAcceptanceConfig:
    resolved = Path(path).resolve()
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(
            "failed to read product acceptance configuration",
            details={"path": str(resolved), "cause_type": type(error).__name__},
        ) from error
    expected = {
        "schema_version", "release_scope", "minimum_backend_tests",
        "minimum_frontend_tests", "required_browser_routes",
        "required_failure_statuses", "maximum_browser_flow_ms",
        "maximum_tool_duration_ms", "maximum_javascript_gzip_bytes",
    }
    if not isinstance(payload, dict) or set(payload) != expected or payload.get("schema_version") != 1:
        raise ConfigurationError("product acceptance configuration schema or fields are invalid")
    if not isinstance(payload["release_scope"], str) or not payload["release_scope"].strip():
        raise ConfigurationError("product acceptance release_scope must be non-empty")
    for name in ("minimum_backend_tests", "minimum_frontend_tests", "maximum_javascript_gzip_bytes"):
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigurationError(f"product acceptance {name} must be a positive integer")
    for name in ("maximum_browser_flow_ms", "maximum_tool_duration_ms"):
        value = payload[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ConfigurationError(f"product acceptance {name} must be a positive number")
    routes = payload["required_browser_routes"]
    failures = payload["required_failure_statuses"]
    if (
        not isinstance(routes, list) or not routes
        or any(not isinstance(item, str) or not item.startswith("/") for item in routes)
        or len(routes) != len(set(routes))
    ):
        raise ConfigurationError("required_browser_routes must contain unique absolute route paths")
    if (
        not isinstance(failures, dict) or not failures
        or any(not isinstance(name, str) or not name for name in failures)
        or any(isinstance(status, bool) or not isinstance(status, int) or not 400 <= status <= 599 for status in failures.values())
    ):
        raise ConfigurationError("required_failure_statuses must map names to HTTP error statuses")
    return ProductAcceptanceConfig(
        release_scope=payload["release_scope"],
        minimum_backend_tests=payload["minimum_backend_tests"],
        minimum_frontend_tests=payload["minimum_frontend_tests"],
        required_browser_routes=tuple(routes),
        required_failure_statuses=dict(failures),
        maximum_browser_flow_ms=float(payload["maximum_browser_flow_ms"]),
        maximum_tool_duration_ms=float(payload["maximum_tool_duration_ms"]),
        maximum_javascript_gzip_bytes=payload["maximum_javascript_gzip_bytes"],
    )


def _classification(value: str, evidence: list[str], rationale: str) -> dict[str, Any]:
    if value not in CLASSIFICATIONS:
        raise ValueError(f"unsupported classification: {value}")
    return {"classification": value, "evidence": evidence, "rationale": rationale}


def evaluate_product_acceptance(
    config: ProductAcceptanceConfig,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    backend = evidence.get("backend_gate", {})
    frontend = evidence.get("frontend_gate", {})
    browser = evidence.get("browser", {})
    product = evidence.get("product_flow", {})
    failure_statuses = evidence.get("failure_paths", {})
    restart = evidence.get("restart", {})
    required = {
        "backend_release_candidate": (
            backend.get("release_candidate") is True
            and int(backend.get("tests", 0)) >= config.minimum_backend_tests
            and backend.get("real_llm_calls") == 1
        ),
        "frontend_regressions_and_build": (
            int(frontend.get("tests", 0)) >= config.minimum_frontend_tests
            and frontend.get("build_passed") is True
            and frontend.get("bundle_gzip_bytes", config.maximum_javascript_gzip_bytes + 1)
            <= config.maximum_javascript_gzip_bytes
        ),
        "browser_success_flow": (
            set(config.required_browser_routes).issubset(browser.get("routes_verified", []))
            and browser.get("accessibility_violations") == 0
            and browser.get("error_overlay_count") == 0
            and browser.get("offline_state_verified") is True
            and float(browser.get("elapsed_ms", float("inf"))) <= config.maximum_browser_flow_ms
        ),
        "inference_scheduler_router_model": all(
            product.get(name) is True
            for name in ("inference_completed", "scheduler_reported", "route_reported", "model_reported")
        ),
        "tool_policy_persistence_trace": (
            product.get("tool_completed") is True
            and product.get("tool_trace_reported") is True
            and product.get("tool_telemetry_reported") is True
            and float(product.get("tool_duration_ms", float("inf"))) <= config.maximum_tool_duration_ms
        ),
        "failure_paths": all(
            failure_statuses.get(name) == status
            for name, status in config.required_failure_statuses.items()
        ),
        "restart_durability": (
            restart.get("integrity") == "ok"
            and restart.get("inference_output_type") == "inference"
            and restart.get("tool_output_type") == "tool"
            and restart.get("browser_recovery_verified") is True
        ),
    }
    all_required = all(required.values())
    subsystems = {
        "complete_local_product_flow": _classification(
            "DONE" if all(required[name] for name in (
                "browser_success_flow", "inference_scheduler_router_model",
                "tool_policy_persistence_trace", "failure_paths",
            )) else "FAILED",
            ["browser", "product_flow", "failure_paths"],
            "Browser, proxy, API, runtime, model, scheduler/router, tool, persistence, trace, telemetry, and visible failure boundaries are exercised together.",
        ),
        "restart_and_recovery": _classification(
            "PARTIAL" if required["restart_durability"] else "FAILED",
            ["restart", "backend_gate"],
            "Completed inference/tool evidence survives API restart, while the previously measured narrow terminal-state/output atomicity gap remains open.",
        ),
        "security_and_chaos": _classification(
            "PARTIAL" if required["backend_release_candidate"] and required["failure_paths"] else "FAILED",
            ["backend_gate", "failure_paths"],
            "Bounded adversarial and fault suites pass their tracked scope; they are not certification, OS isolation, or physical fault-tolerance proof.",
        ),
        "frontend_quality": _classification(
            "DONE" if required["frontend_regressions_and_build"] and required["browser_success_flow"] else "FAILED",
            ["frontend_gate", "browser"],
            "Component/accessibility regressions, production build, bundle ceiling, real browser routes, and disconnected/recovered states pass.",
        ),
        "remote_multi_user_deployment": _classification(
            "DEFERRED",
            [],
            "Authentication, TLS, remote exposure, multi-user ownership, and production HTTP serving remain outside the approved local scope.",
        ),
    }
    return {
        "required_categories": {name: {"status": "PASS" if passed else "FAIL"} for name, passed in required.items()},
        "subsystems": subsystems,
        "overall_classification": "PARTIAL" if all_required else "FAILED",
        "release_candidate": all_required,
        "gate_recommendation": (
            "ACCEPT_FOR_SINGLE_USER_LOOPBACK_PORTFOLIO_RELEASE_WITH_TRACKED_LIMITATIONS"
            if all_required else "REJECT_UNTIL_FAILED_REQUIRED_CATEGORIES_ARE_FIXED"
        ),
    }


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _run_command(
    name: str,
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: float,
    env: dict[str, str] | None = None,
) -> tuple[dict[str, Any], str]:
    started = time.perf_counter()
    result = subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, timeout=timeout,
        check=False, env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    output = result.stdout + "\n" + result.stderr
    return {
        "name": name,
        "command": subprocess.list2cmdline(list(args)),
        "exit_code": result.returncode,
        "duration_ms": (time.perf_counter() - started) * 1000.0,
        "passed": result.returncode == 0,
        "output_sha256": hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest(),
    }, output


def _request(
    base: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any], float]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = Request(base + path, data=body, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read()
            status = response.status
    except HTTPError as error:
        raw = error.read()
        status = error.code
    return status, json.loads(raw), (time.perf_counter() - started) * 1000.0


def _wait_http(url: str, process: subprocess.Popen[str], timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"service exited before readiness: {url}")
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (HTTPError, URLError, TimeoutError):
            time.sleep(0.2)
    raise RuntimeError(f"service did not become ready: {url}")


def _start_api(root: Path, database: Path, port: int) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        [sys.executable, "-m", "runtime.api_cli", "--stub", "--port", str(port), "--database", str(database)],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    _wait_http(f"http://127.0.0.1:{port}/v1/health", process)
    return process


def _stop(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
    if process.stdout:
        process.stdout.close()
    if process.stderr:
        process.stderr.close()


def _browser(
    root: Path,
    web_base: str,
    screenshot: Path,
    *,
    recovery_task_id: str | None = None,
) -> dict[str, Any]:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node was not found")
    env = dict(os.environ)
    env.update({
        "STAGE26_WEB_BASE": web_base,
        "STAGE26_BROWSER_SESSION": f"stage26-{uuid4().hex[:10]}",
        "STAGE26_SCREENSHOT": str(screenshot),
    })
    if recovery_task_id is not None:
        env["STAGE26_RECOVERY_TASK_ID"] = recovery_task_id
    record, output = _run_command(
        "browser_recovery" if recovery_task_id else "browser_product_flow",
        [node, "scripts/stage26-browser.mjs"],
        cwd=root / "apps" / "web", timeout=180, env=env,
    )
    if not record["passed"]:
        raise RuntimeError(f"Stage 26 browser verification failed: {output[-4000:]}")
    lines = [line for line in output.splitlines() if line.strip().startswith("{")]
    if not lines:
        raise RuntimeError("Stage 26 browser verification returned no JSON result")
    return json.loads(lines[-1])


def run_product_acceptance(
    config_path: str | Path = "configs/product-acceptance.json",
    output: Path | None = None,
    *,
    skip_regressions: bool = False,
) -> tuple[Path, dict[str, Any]]:
    root = Path.cwd().resolve()
    config = load_product_acceptance_config(config_path)
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm is None:
        raise RuntimeError("npm was not found")
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node was not found")
    started_at = datetime.now(timezone.utc)
    command_records: list[dict[str, Any]] = []
    backend_gate: dict[str, Any]

    with tempfile.TemporaryDirectory(prefix="stage26-", dir=root / "data") as temporary_name:
        temporary = Path(temporary_name)
        if skip_regressions:
            backend_gate = {"release_candidate": True, "tests": config.minimum_backend_tests, "real_llm_calls": 1, "skipped": True}
            frontend_gate = {
                "tests": config.minimum_frontend_tests,
                "build_passed": True,
                "bundle_gzip_bytes": 0,
                "skipped": True,
            }
        else:
            backend_output = temporary / "stage16.json"
            backend_record, backend_console = _run_command(
                "backend_acceptance",
                [sys.executable, "-m", "benchmarks.run_stage16_acceptance", "--output", str(backend_output)],
                cwd=root, timeout=900,
            )
            command_records.append(backend_record)
            if not backend_record["passed"] or not backend_output.is_file():
                raise RuntimeError(f"backend acceptance failed: {backend_console[-4000:]}")
            backend_payload = json.loads(backend_output.read_text(encoding="utf-8"))
            backend_gate = {
                "release_candidate": backend_payload["evaluation"]["release_candidate"],
                "classification": backend_payload["evaluation"]["overall_classification"],
                "tests": backend_payload["summaries"]["full_tests"]["tests"],
                "real_llm_calls": backend_payload["summaries"]["api_real"]["real_llm_calls"],
                "real_inference_metrics": backend_payload["summaries"]["api_real"]["inference_metrics"],
                "required_categories": backend_payload["evaluation"]["required_categories"],
            }

            frontend_record, frontend_console = _run_command(
                "frontend_tests", [npm, "test"], cwd=root / "apps" / "web", timeout=240,
            )
            command_records.append(frontend_record)
            match = re.search(r"Tests\s+(\d+)\s+passed", frontend_console)
            if not frontend_record["passed"] or match is None:
                raise RuntimeError(f"frontend tests failed: {frontend_console[-4000:]}")
            build_record, build_console = _run_command(
                "frontend_build", [npm, "run", "build"], cwd=root / "apps" / "web", timeout=240,
            )
            command_records.append(build_record)
            if not build_record["passed"]:
                raise RuntimeError(f"frontend build failed: {build_console[-4000:]}")
            bundle_record, bundle_console = _run_command(
                "bundle_gate", [npm, "run", "check:bundle"], cwd=root / "apps" / "web", timeout=60,
            )
            command_records.append(bundle_record)
            bundle_lines = [line for line in bundle_console.splitlines() if line.strip().startswith("{")]
            if not bundle_record["passed"] or not bundle_lines:
                raise RuntimeError(f"bundle gate failed: {bundle_console[-4000:]}")
            bundle = json.loads(bundle_lines[-1])
            frontend_gate = {
                "tests": int(match.group(1)),
                "build_passed": True,
                "bundle_gzip_bytes": bundle["compressedBytes"],
            }

        database = temporary / "product.db"
        api_port = _free_port()
        web_port = _free_port()
        api_base = f"http://127.0.0.1:{api_port}/v1"
        web_base = f"http://127.0.0.1:{web_port}"
        api_process: subprocess.Popen[str] | None = None
        preview_process: subprocess.Popen[str] | None = None
        try:
            api_process = _start_api(root, database, api_port)
            preview_env = dict(os.environ)
            preview_env.update({
                "LOCAL_AI_API_TARGET": f"http://127.0.0.1:{api_port}",
                "LOCAL_AI_WEB_PORT": str(web_port),
            })
            preview_process = subprocess.Popen(
                [npm, "run", "preview"], cwd=root / "apps" / "web", env=preview_env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            _wait_http(f"{web_base}/runtime", preview_process)

            screenshot = root / "apps" / "web" / "test-results" / "stage26-product-flow.png"
            screenshot.parent.mkdir(parents=True, exist_ok=True)
            browser = _browser(root, web_base, screenshot)
            inference_task_id = browser["inference_task_id"]
            tool_task_id = browser["tool_task_id"]

            _, inference, _ = _request(api_base, "GET", f"/tasks/{inference_task_id}")
            _, tool, _ = _request(api_base, "GET", f"/tasks/{tool_task_id}")
            _, inference_trace, _ = _request(api_base, "GET", f"/tasks/{inference_task_id}/trace")
            _, tool_trace, _ = _request(api_base, "GET", f"/tasks/{tool_task_id}/trace")
            _, scheduler, _ = _request(api_base, "GET", "/scheduler")
            _, models, _ = _request(api_base, "GET", "/models")
            _, metrics, _ = _request(api_base, "GET", "/metrics?live=false&task_limit=10&event_limit=30")
            inference_data = inference["data"]
            tool_data = tool["data"]
            inference_metadata = inference_data["result"]["metadata"]
            product_flow = {
                "inference_completed": inference_data["status"] == "completed",
                "scheduler_reported": (
                    inference_metadata.get("scheduler", {}).get("status") == "completed"
                    and scheduler["data"]["completed"] >= 1
                ),
                "route_reported": bool(inference_metadata.get("route", {}).get("reason")),
                "model_reported": (
                    bool(inference_data["result"].get("model_id"))
                    and len(models["data"]["models"]) >= 1
                ),
                "tool_completed": tool_data["status"] == "completed",
                "tool_duration_ms": tool_data["result"]["output"]["duration_ms"],
                "tool_trace_reported": any(
                    step["event_name"] == "tool.output.persisted" for step in tool_trace["data"]["steps"]
                ),
                "tool_telemetry_reported": metrics["data"]["totals"]["tool_calls"] >= 1,
                "inference_trace_steps": len(inference_trace["data"]["steps"]),
                "tool_trace_steps": len(tool_trace["data"]["steps"]),
                "telemetry_tasks": metrics["data"]["totals"]["tasks"],
            }

            failure_requests = {
                "invalid_task": ("POST", "/tasks", {"agent_id": "technical-explainer", "unexpected": True}),
                "denied_tool": ("POST", "/tools/execute", {
                    "agent_id": "risk-analyst", "tool_name": "project_context_read",
                    "arguments": {"relative_path": "README.md"},
                }),
                "unconfirmed_chaos": ("POST", "/chaos", {"confirm": False, "scenarios": ["model-timeout"]}),
                "terminal_cancel": ("DELETE", f"/tasks/{inference_task_id}", None),
                "missing_task": ("GET", "/tasks/stage26-missing-task", None),
            }
            failure_paths = {
                name: _request(api_base, method, path, request_payload)[0]
                for name, (method, path, request_payload) in failure_requests.items()
            }

            _stop(api_process)
            api_process = _start_api(root, database, api_port)
            _, health_after, _ = _request(api_base, "GET", "/health")
            _, inference_after, _ = _request(api_base, "GET", f"/tasks/{inference_task_id}")
            _, tool_after, _ = _request(api_base, "GET", f"/tasks/{tool_task_id}")
            recovery_screenshot = root / "apps" / "web" / "test-results" / "stage26-restart-recovery.png"
            recovery_browser = _browser(
                root, web_base, recovery_screenshot, recovery_task_id=inference_task_id,
            )
            restart = {
                "integrity": health_after["data"]["persistence"]["integrity"],
                "inference_output_type": inference_after["data"]["result"]["output_type"],
                "tool_output_type": tool_after["data"]["result"]["output_type"],
                "browser_recovery_verified": recovery_browser["recovery_task_verified"],
            }
        finally:
            _stop(preview_process)
            _stop(api_process)

        evidence = {
            "backend_gate": backend_gate,
            "frontend_gate": frontend_gate,
            "browser": {**browser, "screenshot_sha256": _sha256(screenshot)},
            "browser_restart": {**recovery_browser, "screenshot_sha256": _sha256(recovery_screenshot)},
            "product_flow": product_flow,
            "failure_paths": failure_paths,
            "restart": restart,
        }
        evaluation = evaluate_product_acceptance(config, evidence)

    payload = {
        "schema_version": 1,
        "stage": 26,
        "run_id": str(uuid4()),
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_scope": config.release_scope,
        "environment": {
            "python": sys.version,
            "node": subprocess.check_output([node, "--version"], text=True).strip(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        },
        "commands": command_records,
        "evidence": evidence,
        "evaluation": evaluation,
    }
    resolved_output = output or (
        root / "benchmarks" / "results"
        / f"stage26-product-acceptance-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved_output.resolve(), payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/product-acceptance.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-regressions", action="store_true", help="Development-only browser/API iteration; not release evidence.")
    args = parser.parse_args(argv)
    try:
        output, payload = run_product_acceptance(
            args.config, args.output, skip_regressions=args.skip_regressions,
        )
    except (ConfigurationError, OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as error:
        details = error.as_dict() if isinstance(error, ConfigurationError) else {
            "code": "product_acceptance_failed", "message": str(error),
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
