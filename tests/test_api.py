from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path

from runtime.api import RuntimeApiService, build_api_server, load_api_config
from runtime.engine import AgentRuntime
from runtime.errors import InferenceCancelledError
from runtime.errors import ConfigurationError
from runtime.factory import build_stage15_stub_runtime
from runtime.models import InferenceMetrics, InferenceResult
from runtime.security import GuardedInferenceBackend


class ApiHarness:
    def __init__(self, directory: Path, runtime: AgentRuntime | None = None) -> None:
        self.runtime = runtime or build_stage15_stub_runtime(directory / "api.db")
        self.runtime.start()
        self.config = replace(
            load_api_config(),
            port=0,
            stream_poll_ms=5,
            stream_timeout_ms=5_000,
            security_results_directory=directory,
        )
        self.service = RuntimeApiService(
            self.runtime,
            self.config,
            chaos_data_directory=directory,
        )
        self.server = build_api_server(self.service, self.config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        *,
        raw: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        body = raw
        resolved_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        if body is not None:
            resolved_headers.setdefault("Content-Type", "application/json")
            resolved_headers.setdefault("Content-Length", str(len(body)))
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=15)
        connection.request(method, path, body=body, headers=resolved_headers)
        response = connection.getresponse()
        content = response.read()
        response_headers = {name.lower(): value for name, value in response.getheaders()}
        connection.close()
        return response.status, response_headers, content

    def json(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict, dict[str, str]]:
        status, headers, body = self.request(method, path, payload)
        return status, json.loads(body), headers

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.service.shutdown()
        self.runtime.shutdown()


class Stage15ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.api = ApiHarness(self.directory)

    def tearDown(self) -> None:
        self.api.close()
        self.temp.cleanup()

    def _create(self, objective: str = "Explain why bounded local APIs are useful.") -> dict:
        status, payload, _ = self.api.json("POST", "/v1/tasks", {
            "agent_id": "technical-explainer",
            "objective": objective,
            "workload": "interactive",
            "timeout_ms": 2_000,
        })
        self.assertEqual(status, 202)
        return payload["data"]

    def _terminal(self, task_id: str) -> dict:
        for _ in range(200):
            status, payload, _ = self.api.json("GET", f"/v1/tasks/{task_id}")
            self.assertEqual(status, 200)
            if payload["data"]["status"] in {"completed", "failed", "cancelled", "timed_out"}:
                return payload["data"]
            time.sleep(0.01)
        self.fail("API task did not become terminal")

    def test_api_configuration_rejects_non_loopback_and_non_object_json(self) -> None:
        with self.assertRaises(ConfigurationError):
            replace(load_api_config(), host="0.0.0.0")
        invalid = self.directory / "invalid-api.json"
        invalid.write_text("[]", encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            load_api_config(invalid)

    def test_discovery_health_openapi_and_no_static_file_serving(self) -> None:
        status, discovery, headers = self.api.json("GET", "/v1")
        self.assertEqual(status, 200)
        self.assertEqual(discovery["data"]["stage"], 15)
        self.assertEqual(headers["x-content-type-options"], "nosniff")
        status, health, _ = self.api.json("GET", "/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["data"]["persistence"]["integrity"], "ok")
        status, openapi, _ = self.api.json("GET", "/v1/openapi.json")
        self.assertEqual(status, 200)
        self.assertEqual(openapi["openapi"], "3.1.0")
        self.assertIn("get", openapi["paths"]["/v1/chaos"])
        self.assertIn("post", openapi["paths"]["/v1/security"])
        self.assertIn("post", openapi["paths"]["/v1/tools/execute"])
        status, payload, _ = self.api.json("GET", "/README.md")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "task_not_found")

    def test_create_inspect_and_stream_task_over_real_socket(self) -> None:
        accepted = self._create()
        task_id = accepted["task_id"]
        status, headers, body = self.api.request("GET", f"/v1/tasks/{task_id}/events")
        self.assertEqual(status, 200)
        self.assertTrue(headers["content-type"].startswith("text/event-stream"))
        stream = body.decode("utf-8")
        self.assertIn("event: lifecycle", stream)
        self.assertIn("event: task", stream)
        self.assertIn("event: end", stream)
        result = self._terminal(task_id)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["durable_state"], "completed")
        self.assertEqual(result["result"]["metadata"]["real_llm_calls"], 0)

    def test_component_inspection_omits_system_prompts_and_model_paths(self) -> None:
        for path in ("/v1/agents", "/v1/scheduler", "/v1/hardware", "/v1/models", "/v1/metrics?live=false"):
            status, payload, _ = self.api.json("GET", path)
            self.assertEqual(status, 200, path)
            serialized = json.dumps(payload)
            self.assertNotIn("system_prompt", serialized)
        _, agents, _ = self.api.json("GET", "/v1/agents")
        self.assertEqual(len(agents["data"]["agents"]), 2)
        _, models, _ = self.api.json("GET", "/v1/models")
        self.assertIn("artifact", models["data"]["models"][0])
        self.assertNotIn("path", models["data"]["models"][0])

    def test_trace_is_payload_redacted_and_replayable(self) -> None:
        terminal = self._terminal(self._create()["task_id"])
        task_id = terminal["task_id"]
        status, trace, _ = self.api.json("GET", f"/v1/tasks/{task_id}/trace")
        self.assertEqual(status, 200)
        self.assertNotIn("input", trace["data"]["steps"][0])
        self.assertNotIn("output", trace["data"]["steps"][0])
        run_id = trace["data"]["run"]["run_id"]
        status, replay, _ = self.api.json("POST", f"/v1/traces/{run_id}/replay", {})
        self.assertEqual(status, 200)
        self.assertTrue(replay["data"]["integrity_valid"])

    def test_catalogued_tool_executes_through_api_and_denies_cross_agent_grant(self) -> None:
        status, catalog, _ = self.api.json("GET", "/v1/tools")
        self.assertEqual(status, 200)
        self.assertEqual({item["name"] for item in catalog["data"]["tools"]}, {
            "project_context_read", "risk_register_read",
        })
        project_tool = next(
            item for item in catalog["data"]["tools"] if item["name"] == "project_context_read"
        )
        self.assertEqual(project_tool["authorized_agent_ids"], ["technical-explainer"])
        self.assertTrue(project_tool["permission"]["read_only"])
        self.assertTrue(project_tool["permission"]["path_restricted"])

        status, executed, _ = self.api.json("POST", "/v1/tools/execute", {
            "agent_id": "technical-explainer",
            "tool_name": "project_context_read",
            "arguments": {"relative_path": "README.md", "max_characters": 120},
        })
        self.assertEqual(status, 200)
        result = executed["data"]
        self.assertTrue(result["success"])
        self.assertEqual(result["final_state"], "completed")
        self.assertEqual(result["data"]["relative_path"], "README.md")
        self.assertLessEqual(result["data"]["characters_returned"], 120)

        status, inspected, _ = self.api.json("GET", f"/v1/tasks/{result['task_id']}")
        self.assertEqual(status, 200)
        self.assertEqual(inspected["data"]["result"]["output_type"], "tool")
        status, trace, _ = self.api.json("GET", f"/v1/tasks/{result['task_id']}/trace")
        self.assertEqual(status, 200)
        self.assertTrue(any(step["event_name"] == "tool.output.persisted" for step in trace["data"]["steps"]))

        status, denied, _ = self.api.json("POST", "/v1/tools/execute", {
            "agent_id": "risk-analyst",
            "tool_name": "project_context_read",
            "arguments": {"relative_path": "README.md"},
        })
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"]["code"], "tool_permission_denied")

    def test_completed_task_remains_inspectable_after_api_restart(self) -> None:
        task_id = self._terminal(self._create()["task_id"])["task_id"]
        self.api.close()
        self.api = ApiHarness(self.directory)
        status, inspected, _ = self.api.json("GET", f"/v1/tasks/{task_id}")
        self.assertEqual(status, 200)
        self.assertEqual(inspected["data"]["status"], "completed")
        self.assertEqual(inspected["data"]["durable_state"], "completed")
        self.assertEqual(inspected["data"]["result"]["output_type"], "inference")
        self.assertIn("STUB (no LLM inference):", inspected["data"]["result"]["output"])
        self.assertEqual(inspected["data"]["result"]["final_state"], "completed")
        self.assertIsInstance(inspected["data"]["result"]["metadata"], dict)
        self.assertGreater(len(inspected["data"]["result"]["state_history"]), 0)

    def test_transport_and_security_validation_fail_closed(self) -> None:
        status, _, body = self.api.request(
            "POST",
            "/v1/tasks",
            raw=b'{"agent_id":"technical-explainer","agent_id":"risk-summarizer"}',
        )
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["error"]["code"], "api_request_invalid")
        status, payload, _ = self.api.json("GET", "/v1/health?unexpected=true")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "api_request_invalid")
        status, payload, _ = self.api.json("POST", "/v1/tasks", {
            "agent_id": "technical-explainer",
            "objective": "x" * 4_097,
        })
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"]["code"], "security_policy_denied")
        self.assertEqual(self.api.runtime.components.persistence.table_counts()["tasks"], 0)
        oversized = b"{" + b" " * self.api.config.max_request_bytes + b"}"
        status, _, body = self.api.request("POST", "/v1/tasks", raw=oversized)
        self.assertEqual(status, 413)
        self.assertEqual(json.loads(body)["error"]["details"]["maximum_bytes"], 65_536)

    def test_confirmed_chaos_and_security_experiments_are_catalogued_isolated_and_retrievable(self) -> None:
        status, payload, _ = self.api.json("GET", "/v1/chaos")
        self.assertEqual(status, 200)
        self.assertFalse(payload["data"]["armed_by_default"])
        self.assertEqual(payload["data"]["maximum_scenarios_per_run"], 3)
        self.assertEqual(len(payload["data"]["scenarios"]), 9)
        status, payload, _ = self.api.json("POST", "/v1/chaos", {
            "confirm": False,
            "scenarios": ["model-timeout"],
        })
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "api_request_invalid")
        status, payload, _ = self.api.json("POST", "/v1/chaos", {
            "confirm": True,
            "scenarios": ["model-timeout"],
        })
        self.assertEqual(status, 200)
        self.assertTrue(payload["data"]["report"]["scenarios"][0]["expected_outcome_met"])
        self.assertEqual(self.api.runtime.status.value, "running")

        status, payload, _ = self.api.json("GET", "/v1/security")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["maximum_cases_per_run"], 14)
        self.assertEqual(len(payload["data"]["cases"]), 14)
        self.assertIn("not a production penetration test", payload["data"]["scope"])
        status, payload, _ = self.api.json("POST", "/v1/security", {
            "confirm": False,
            "cases": ["prompt-injection"],
        })
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "api_request_invalid")
        status, payload, _ = self.api.json("POST", "/v1/security", {
            "confirm": True,
            "cases": ["not-a-security-case"],
        })
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["details"]["case_ids"], ["not-a-security-case"])
        status, payload, _ = self.api.json("POST", "/v1/security", {
            "confirm": True,
            "cases": ["prompt-injection", "tool-escalation"],
        })
        self.assertEqual(status, 200)
        result_id = payload["data"]["result_id"]
        self.assertEqual(payload["data"]["report"]["summary"]["passed"], 2)
        self.assertEqual(payload["data"]["report"]["summary"]["failed"], 0)
        self.assertEqual(payload["data"]["report"]["summary"]["real_llm_calls"], 0)
        self.assertTrue((self.directory / f"{result_id}.json").is_file())
        self.assertEqual(self.api.runtime.status.value, "running")
        status, payload, _ = self.api.json("GET", "/v1/security/results")
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["result_id"], result_id)
        self.assertEqual(payload["data"]["report"]["summary"]["failed"], 0)


class SlowInferenceBackend:
    name = "stage15-cancellable-test"

    def __init__(self) -> None:
        self.started = False

    def start(self) -> None:
        self.started = True

    def shutdown(self) -> None:
        self.started = False

    def generate(self, request, cancellation=None) -> InferenceResult:
        for _ in range(200):
            if cancellation is not None and cancellation.is_cancelled:
                raise InferenceCancelledError("test inference cancelled")
            time.sleep(0.005)
        return InferenceResult("late", request.model_id, self.name, metrics=InferenceMetrics(total_ms=1_000))

    def stream(self, request, cancellation=None):
        raise NotImplementedError


class Stage15CancellationApiTests(unittest.TestCase):
    def test_delete_cooperatively_cancels_active_task(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            base = build_stage15_stub_runtime(directory / "cancel.db")
            runtime = AgentRuntime(
                config=base.config,
                components=replace(
                    base.components,
                    inference=GuardedInferenceBackend(SlowInferenceBackend(), base.components.security),
                ),
            )
            api = ApiHarness(directory, runtime)
            try:
                status, accepted, _ = api.json("POST", "/v1/tasks", {
                    "agent_id": "technical-explainer",
                    "objective": "Cancellation boundary test.",
                })
                self.assertEqual(status, 202)
                task_id = accepted["data"]["task_id"]
                status, cancelled, _ = api.json("DELETE", f"/v1/tasks/{task_id}")
                self.assertEqual(status, 202)
                self.assertTrue(cancelled["data"]["cancellation_requested"])
                for _ in range(200):
                    _, inspected, _ = api.json("GET", f"/v1/tasks/{task_id}")
                    if inspected["data"]["status"] == "cancelled":
                        break
                    time.sleep(0.01)
                self.assertEqual(inspected["data"]["status"], "cancelled")
                self.assertEqual(inspected["data"]["durable_state"], "cancelled")
            finally:
                api.close()


if __name__ == "__main__":
    unittest.main()
