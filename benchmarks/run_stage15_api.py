"""Exercise Stage 15 exclusively through its external HTTP/SSE contract."""

from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def _ready(process: subprocess.Popen[str]) -> dict[str, Any]:
    lines: queue.Queue[str] = queue.Queue()

    def read_line() -> None:
        assert process.stdout is not None
        lines.put(process.stdout.readline())

    threading.Thread(target=read_line, daemon=True).start()
    try:
        line = lines.get(timeout=20)
    except queue.Empty as error:
        raise RuntimeError("API process did not publish readiness within 20 seconds") from error
    if not line:
        stderr = process.stderr.read() if process.stderr else ""
        raise RuntimeError(f"API process exited before readiness: {stderr}")
    payload = json.loads(line)
    if payload.get("event") != "api.ready":
        raise RuntimeError(f"unexpected API readiness payload: {payload}")
    return payload


def _request(
    base: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any], float]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    started = perf_counter()
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read()
            status = response.status
    except HTTPError as error:
        body = error.read()
        status = error.code
    elapsed = (perf_counter() - started) * 1000.0
    return status, json.loads(body), elapsed


def _stream(base: str, task_id: str) -> tuple[int, str, float]:
    started = perf_counter()
    with urlopen(base + f"/tasks/{task_id}/events", timeout=60) as response:
        body = response.read().decode("utf-8")
        status = response.status
    return status, body, (perf_counter() - started) * 1000.0


def run(output: Path | None = None, *, stub: bool = True) -> tuple[Path, dict[str, Any]]:
    database = (Path("data") / f"stage15-api-{uuid4().hex}.db").resolve()
    command = [
        sys.executable,
        "-m",
        "runtime.api_cli",
        "--port",
        "0",
        "--database",
        str(database),
    ]
    if stub:
        command.insert(3, "--stub")
    process = subprocess.Popen(
        command,
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    started_at = datetime.now(timezone.utc)
    operations: dict[str, dict[str, Any]] = {}
    try:
        ready = _ready(process)
        base = ready["base_url"]

        def call(name: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
            status, body, duration_ms = _request(base, method, path, payload)
            operations[name] = {"status": status, "duration_ms": duration_ms}
            if status >= 400:
                raise RuntimeError(f"{name} failed with {status}: {body}")
            return body

        discovery = call("discovery", "GET", "")
        call("openapi", "GET", "/openapi.json")
        created = call("task_create", "POST", "/tasks", {
            "agent_id": "technical-explainer",
            "objective": "Explain the Stage 15 external runtime boundary in two concise points.",
            "workload": "interactive",
            "timeout_ms": 5_000,
        })
        task_id = created["data"]["task_id"]
        stream_status, stream_body, stream_ms = _stream(base, task_id)
        operations["task_events"] = {"status": stream_status, "duration_ms": stream_ms}
        task = call("task_inspect", "GET", f"/tasks/{task_id}")
        agents = call("agents", "GET", "/agents")
        scheduler = call("scheduler", "GET", "/scheduler")
        hardware = call("hardware", "GET", "/hardware")
        models = call("models", "GET", "/models")
        metrics = call("metrics", "GET", "/metrics?live=true&task_limit=10&event_limit=30")
        trace = call("task_trace", "GET", f"/tasks/{task_id}/trace")
        run_id = trace["data"]["run"]["run_id"]
        replay = call("trace_replay", "POST", f"/traces/{run_id}/replay", {})
        chaos_denied_status, chaos_denied, chaos_denied_ms = _request(
            base, "POST", "/chaos", {"confirm": False, "scenarios": ["model-timeout"]}
        )
        operations["chaos_unconfirmed"] = {"status": chaos_denied_status, "duration_ms": chaos_denied_ms}
        chaos = call("chaos_confirmed", "POST", "/chaos", {
            "confirm": True,
            "scenarios": ["model-timeout"],
        })
        security = call("security_results", "GET", "/security/results")
        health = call("health", "GET", "/health")

        required_statuses = {name: item["status"] for name, item in operations.items()}
        passed = (
            all(status in {200, 202} for name, status in required_statuses.items() if name != "chaos_unconfirmed")
            and chaos_denied_status == 400
            and task["data"]["status"] == "completed"
            and "event: lifecycle" in stream_body
            and "event: task" in stream_body
            and replay["data"]["integrity_valid"] is True
            and chaos["data"]["report"]["scenarios"][0]["expected_outcome_met"] is True
            and security["data"]["report"]["summary"]["failed"] == 0
            and health["data"]["persistence"]["integrity"] == "ok"
        )
        report = {
            "stage": 15,
            "run_id": str(uuid4()),
            "started_at_utc": started_at.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "passed": passed,
            "process_boundary": {
                "command": (
                    "python -m runtime.api_cli --stub --port 0 --database <unique>"
                    if stub
                    else "python -m runtime.api_cli --port 0 --database <unique>"
                ),
                "client": "Python standard-library HTTP client",
                "direct_runtime_calls_after_launch": 0,
                "real_llm_calls": int(task["data"]["result"]["metadata"].get("real_llm_calls", 0)),
                "ready": ready,
            },
            "operations": operations,
            "evidence": {
                "api_stage": discovery["data"]["stage"],
                "task_id": task_id,
                "task_status": task["data"]["status"],
                "durable_state": task["data"]["durable_state"],
                "model_id": task["data"]["result"]["model_id"],
                "backend_name": task["data"]["result"]["backend_name"],
                "selected_profile": (
                    task["data"]["result"]["metadata"].get("profile_selection") or {}
                ).get("selected_profile"),
                "inference_metrics": task["data"]["result"]["inference_metrics"],
                "sse_lifecycle_events": stream_body.count("event: lifecycle"),
                "sse_terminal_event": "event: task" in stream_body,
                "agent_count": len(agents["data"]["agents"]),
                "scheduler_policy": scheduler["data"]["policy"],
                "hardware_cpu_source": hardware["data"]["cpu"]["source"],
                "model_count": len(models["data"]["models"]),
                "metrics_task_total": metrics["data"]["totals"]["tasks"],
                "trace_steps": len(trace["data"]["steps"]),
                "trace_payloads_omitted": "input" not in trace["data"]["steps"][0],
                "replay_integrity_valid": replay["data"]["integrity_valid"],
                "unconfirmed_chaos_code": chaos_denied["error"]["code"],
                "chaos_expected_outcome_met": chaos["data"]["report"]["scenarios"][0]["expected_outcome_met"],
                "security_failed": security["data"]["report"]["summary"]["failed"],
                "database_integrity": health["data"]["persistence"]["integrity"],
            },
            "component_roles": {
                "http_adapter": "validates bounded requests and maps typed runtime errors to versioned JSON",
                "task_manager": "owns bounded asynchronous task lifecycle and cooperative cancellation",
                "sse_stream": "publishes ordered lifecycle evidence and one terminal task snapshot",
                "inspection_service": "exposes safe agent, scheduler, hardware, model, metrics, and trace views",
                "replay_endpoint": "verifies trace integrity without re-executing side effects or model calls",
                "chaos_endpoint": "requires confirmation and runs only in a separate stub runtime/database",
                "security_results": "returns retained adversarial evidence with its explicit scope disclaimer",
            },
        }
        if not passed:
            raise RuntimeError("Stage 15 API evidence did not satisfy all assertions")
    finally:
        if process.poll() is None:
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

    resolved_output = output or (
        Path("benchmarks/results")
        / f"stage15-api{'-real' if not stub else ''}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved_output.resolve(), report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--real", action="store_true", help="Use the real guarded local llama.cpp composition.")
    args = parser.parse_args()
    try:
        output, report = run(args.output, stub=not args.real)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"code": "stage15_api_benchmark_failed", "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps({"output": str(output), "passed": report["passed"], "operations": len(report["operations"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
