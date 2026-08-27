"""Small checked-in-code OpenAPI description for the Stage 15 contract."""

from __future__ import annotations

from typing import Any


def openapi_document() -> dict[str, Any]:
    json_response = {"description": "JSON response", "content": {"application/json": {}}}
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Local AI Systems Lab API",
            "version": "0.15.0",
            "description": "Loopback-only development API for the complete Stage 15 runtime.",
        },
        "servers": [{"url": "http://127.0.0.1:8765"}],
        "paths": {
            "/v1": {"get": {"summary": "Discover API capabilities", "responses": {"200": json_response}}},
            "/v1/health": {"get": {"summary": "Inspect runtime health", "responses": {"200": json_response}}},
            "/v1/tasks": {"post": {"summary": "Create a task", "responses": {"202": json_response}}},
            "/v1/tasks/{task_id}": {
                "get": {"summary": "Inspect a task", "responses": {"200": json_response}},
                "delete": {"summary": "Cancel an active task", "responses": {"202": json_response}},
            },
            "/v1/tasks/{task_id}/events": {"get": {"summary": "Stream lifecycle events over SSE", "responses": {"200": {"description": "text/event-stream"}}}},
            "/v1/tasks/{task_id}/trace": {"get": {"summary": "Inspect a redacted task trace", "responses": {"200": json_response}}},
            "/v1/agents": {"get": {"summary": "Inspect safe agent metadata", "responses": {"200": json_response}}},
            "/v1/scheduler": {"get": {"summary": "Inspect scheduler state", "responses": {"200": json_response}}},
            "/v1/hardware": {"get": {"summary": "Inspect measured hardware", "responses": {"200": json_response}}},
            "/v1/models": {"get": {"summary": "Inspect model registry and budgets", "responses": {"200": json_response}}},
            "/v1/tools": {"get": {"summary": "Inspect registered bounded tools and exact agent grants", "responses": {"200": json_response}}},
            "/v1/tools/execute": {"post": {"summary": "Execute one agent-authorized bounded tool operation", "responses": {"200": json_response}}},
            "/v1/metrics": {"get": {"summary": "Retrieve unified metrics", "responses": {"200": json_response}}},
            "/v1/traces/{run_id}": {"get": {"summary": "Inspect a redacted trace", "responses": {"200": json_response}}},
            "/v1/traces/{run_id}/replay": {"post": {"summary": "Replay deterministic trace reducers", "responses": {"200": json_response}}},
            "/v1/chaos": {
                "get": {"summary": "Inspect the bounded chaos scenario catalog", "responses": {"200": json_response}},
                "post": {"summary": "Run confirmed isolated chaos scenarios", "responses": {"200": json_response}},
            },
            "/v1/security": {
                "get": {"summary": "Inspect the bounded adversarial case catalog", "responses": {"200": json_response}},
                "post": {"summary": "Run a confirmed deterministic security suite", "responses": {"200": json_response}},
            },
            "/v1/security/results": {"get": {"summary": "Inspect retained security evidence", "responses": {"200": json_response}}},
        },
    }
