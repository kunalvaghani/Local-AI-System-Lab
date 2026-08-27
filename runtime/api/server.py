"""Dependency-free loopback HTTP/JSON and SSE adapter for Stage 15."""

from __future__ import annotations

import json
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from ..errors import (
    AgentNotFoundError,
    ApiCapacityError,
    ApiConflictError,
    ApiRequestError,
    ConfigurationError,
    LabError,
    PolicyDeniedError,
    TaskNotFoundError,
    ToolNotFoundError,
    ValidationError,
)
from ..models import LifecycleEvent
from .config import ApiConfig
from .openapi import openapi_document
from .service import RuntimeApiService


_TASK = re.compile(r"^/v1/tasks/([A-Za-z0-9-]+)$")
_TASK_EVENTS = re.compile(r"^/v1/tasks/([A-Za-z0-9-]+)/events$")
_TASK_TRACE = re.compile(r"^/v1/tasks/([A-Za-z0-9-]+)/trace$")
_TRACE = re.compile(r"^/v1/traces/([A-Za-z0-9-]+)$")
_TRACE_REPLAY = re.compile(r"^/v1/traces/([A-Za-z0-9-]+)/replay$")


def _reject_constant(value: str) -> None:
    raise ApiRequestError("non-finite JSON numbers are not accepted", details={"value": value})


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ApiRequestError("duplicate JSON object key", details={"key": key})
        result[key] = value
    return result


def _event_payload(event: LifecycleEvent) -> dict[str, Any]:
    return {
        "name": event.name,
        "recorded_at_utc": event.recorded_at.isoformat(),
        "agent_id": event.agent_id,
        "task_id": event.task_id,
        "state": event.state.value if event.state else None,
        "data": dict(event.data),
    }


class RuntimeApiHttpServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, config: ApiConfig, service: RuntimeApiService) -> None:
        self.api_config = config
        self.service = service
        super().__init__((config.host, config.port), RuntimeApiHandler)


class RuntimeApiHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "LocalAISystemsLab/0.15"
    sys_version = ""

    @property
    def api_server(self) -> RuntimeApiHttpServer:
        return self.server  # type: ignore[return-value]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_DELETE(self) -> None:
        self._dispatch("DELETE")

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:
        self._method_not_allowed()

    def _dispatch(self, method: str) -> None:
        self._request_id = str(uuid4())
        self.close_connection = True
        try:
            target = urlsplit(self.path)
            query = self._query(target.query)
            path = target.path
            if query and not (
                (method == "GET" and path == "/v1/metrics")
                or (method == "GET" and _TASK_EVENTS.fullmatch(path))
            ):
                raise ApiRequestError("this endpoint does not accept query parameters")
            service = self.api_server.service
            if method == "GET" and path == "/v1":
                self._json(HTTPStatus.OK, service.discovery())
            elif method == "GET" and path == "/v1/health":
                self._json(HTTPStatus.OK, service.health())
            elif method == "GET" and path == "/v1/openapi.json":
                self._json(HTTPStatus.OK, openapi_document(), envelope=False)
            elif method == "POST" and path == "/v1/tasks":
                self._json(HTTPStatus.ACCEPTED, service.create_task(self._json_body(required=True)))
            elif method == "GET" and (match := _TASK.fullmatch(path)):
                self._json(HTTPStatus.OK, service.tasks.inspect(match.group(1)))
            elif method == "DELETE" and (match := _TASK.fullmatch(path)):
                if query:
                    raise ApiRequestError("task cancellation does not accept query parameters")
                self._json(HTTPStatus.ACCEPTED, service.tasks.cancel(match.group(1)))
            elif method == "GET" and (match := _TASK_EVENTS.fullmatch(path)):
                self._stream_events(match.group(1), query)
            elif method == "GET" and (match := _TASK_TRACE.fullmatch(path)):
                self._json(HTTPStatus.OK, service.task_trace(match.group(1)))
            elif method == "GET" and path == "/v1/agents":
                self._json(HTTPStatus.OK, service.agents())
            elif method == "GET" and path == "/v1/scheduler":
                self._json(HTTPStatus.OK, service.scheduler())
            elif method == "GET" and path == "/v1/hardware":
                self._json(HTTPStatus.OK, service.hardware())
            elif method == "GET" and path == "/v1/models":
                self._json(HTTPStatus.OK, service.models())
            elif method == "GET" and path == "/v1/tools":
                self._json(HTTPStatus.OK, service.tools())
            elif method == "POST" and path == "/v1/tools/execute":
                self._json(HTTPStatus.OK, service.execute_tool(self._json_body(required=True)))
            elif method == "GET" and path == "/v1/metrics":
                self._json(HTTPStatus.OK, service.metrics(query))
            elif method == "GET" and (match := _TRACE.fullmatch(path)):
                self._json(HTTPStatus.OK, service.trace(match.group(1)))
            elif method == "POST" and (match := _TRACE_REPLAY.fullmatch(path)):
                self._require_empty_json_body()
                self._json(HTTPStatus.OK, service.replay_trace(match.group(1)))
            elif method == "GET" and path == "/v1/chaos":
                self._json(HTTPStatus.OK, service.chaos_catalog())
            elif method == "POST" and path == "/v1/chaos":
                self._json(HTTPStatus.OK, service.chaos(self._json_body(required=True)))
            elif method == "GET" and path == "/v1/security":
                self._json(HTTPStatus.OK, service.security_catalog())
            elif method == "POST" and path == "/v1/security":
                self._json(HTTPStatus.OK, service.run_security(self._json_body(required=True)))
            elif method == "GET" and path == "/v1/security/results":
                self._json(HTTPStatus.OK, service.security_results())
            elif path in self._known_paths() or self._is_known_pattern(path):
                self._method_not_allowed()
            else:
                raise TaskNotFoundError("API route was not found", details={"path": path})
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception as error:
            self._error(error)

    @staticmethod
    def _known_paths() -> set[str]:
        return {
            "/v1", "/v1/health", "/v1/openapi.json", "/v1/tasks", "/v1/agents",
            "/v1/scheduler", "/v1/hardware", "/v1/models", "/v1/metrics",
            "/v1/tools", "/v1/tools/execute",
            "/v1/chaos", "/v1/security", "/v1/security/results",
        }

    @staticmethod
    def _is_known_pattern(path: str) -> bool:
        return any(pattern.fullmatch(path) for pattern in (_TASK, _TASK_EVENTS, _TASK_TRACE, _TRACE, _TRACE_REPLAY))

    def _query(self, value: str) -> dict[str, str]:
        if not value:
            return {}
        try:
            parsed = parse_qs(value, keep_blank_values=True, max_num_fields=16, strict_parsing=True)
        except ValueError as error:
            raise ApiRequestError("query string is malformed") from error
        duplicates = [key for key, values in parsed.items() if len(values) != 1]
        if duplicates:
            raise ApiRequestError("duplicate query parameter", details={"fields": sorted(duplicates)})
        return {key: values[0] for key, values in parsed.items()}

    def _json_body(self, *, required: bool) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").partition(";")[0].strip().lower()
        if content_type != "application/json":
            raise ApiRequestError("Content-Type must be application/json")
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ApiRequestError("Content-Length is required for JSON requests")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise ApiRequestError("Content-Length is invalid") from error
        if length < 0:
            raise ApiRequestError("Content-Length must not be negative")
        if length > self.api_server.api_config.max_request_bytes:
            self.close_connection = True
            raise ApiRequestError(
                "request body exceeds the configured limit",
                details={"http_status": 413, "maximum_bytes": self.api_server.api_config.max_request_bytes},
            )
        body = self.rfile.read(length)
        if required and not body:
            raise ApiRequestError("JSON request body is required")
        try:
            value = json.loads(
                body.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            ) if body else {}
        except UnicodeDecodeError as error:
            raise ApiRequestError("request body must be UTF-8") from error
        except json.JSONDecodeError as error:
            raise ApiRequestError(
                "request body is not valid JSON",
                details={"line": error.lineno, "column": error.colno},
            ) from error
        if not isinstance(value, dict):
            raise ApiRequestError("top-level JSON value must be an object")
        return value

    def _require_empty_json_body(self) -> None:
        payload = self._json_body(required=False)
        if payload:
            raise ApiRequestError("trace replay body must be an empty JSON object")

    def _json(self, status: HTTPStatus, payload: dict[str, Any], *, envelope: bool = True) -> None:
        value = {"data": payload, "request_id": self._request_id} if envelope else payload
        body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _stream_events(self, task_id: str, query: dict[str, str]) -> None:
        unexpected = set(query) - {"after"}
        if unexpected:
            raise ApiRequestError("unknown event stream query parameter", details={"fields": sorted(unexpected)})
        try:
            after = int(query.get("after", "0"))
        except ValueError as error:
            raise ApiRequestError("after must be a non-negative integer") from error
        if after < 0:
            raise ApiRequestError("after must be a non-negative integer")
        manager = self.api_server.service.tasks
        manager.get(task_id)
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        deadline = time.monotonic() + self.api_server.api_config.stream_timeout_ms / 1000.0
        cursor = after
        while time.monotonic() < deadline:
            events = manager.events(task_id)
            for index, event in enumerate(events[cursor:], start=cursor + 1):
                self._sse(index, "lifecycle", _event_payload(event))
                cursor = index
            record = manager.get(task_id)
            if record.terminal:
                self._sse(cursor + 1, "task", manager.inspect(task_id))
                self._sse(cursor + 2, "end", {"reason": "task_terminal"})
                return
            time.sleep(self.api_server.api_config.stream_poll_ms / 1000.0)
        self._sse(cursor + 1, "end", {"reason": "stream_timeout", "task_continues": True})

    def _sse(self, event_id: int, event_name: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.wfile.write(f"id: {event_id}\nevent: {event_name}\ndata: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    def _method_not_allowed(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self._security_headers()
        body = json.dumps({
            "error": {"code": "method_not_allowed", "message": "HTTP method is not supported", "details": {}},
            "request_id": getattr(self, "_request_id", str(uuid4())),
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_header("Allow", "GET, POST, DELETE")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, error: Exception) -> None:
        if isinstance(error, LabError):
            payload = error.as_dict()
        else:
            payload = {
                "code": "internal_server_error",
                "message": "an unexpected API boundary failure occurred",
                "details": {"cause_type": type(error).__name__},
            }
        if isinstance(error, (TaskNotFoundError, AgentNotFoundError, ToolNotFoundError)):
            status = HTTPStatus.NOT_FOUND
        elif isinstance(error, ApiConflictError):
            status = HTTPStatus.CONFLICT
        elif isinstance(error, ApiCapacityError):
            status = HTTPStatus.TOO_MANY_REQUESTS
        elif isinstance(error, PolicyDeniedError):
            status = HTTPStatus.FORBIDDEN
        elif isinstance(error, ConfigurationError):
            status = HTTPStatus.SERVICE_UNAVAILABLE
        elif isinstance(error, (ApiRequestError, ValidationError)):
            status = HTTPStatus(payload.get("details", {}).get("http_status", 400))
        else:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        body = json.dumps({"error": payload, "request_id": getattr(self, "_request_id", str(uuid4()))}, sort_keys=True, separators=(",", ":")).encode("utf-8")
        try:
            self.send_response(status)
            self._security_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")


def build_api_server(
    service: RuntimeApiService,
    config: ApiConfig,
) -> RuntimeApiHttpServer:
    return RuntimeApiHttpServer(config, service)
