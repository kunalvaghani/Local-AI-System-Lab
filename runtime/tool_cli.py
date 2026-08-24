"""Demonstrate allowed and denied Stage 5 tool requests without loading an LLM."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from .agents import stage3_agents
from .errors import LabError, ToolPermissionDeniedError, ValidationError
from .factory import build_stage1_runtime
from .models import LifecycleEvent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute a validated Stage 5 tool request.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run one permitted request and one expected default-deny request.",
    )
    parser.add_argument(
        "--agent",
        choices=[agent.agent_id for agent in stage3_agents()],
        default="technical-explainer",
    )
    parser.add_argument("--tool", default="project_context_read")
    parser.add_argument(
        "--arguments",
        default='{"relative_path": "README.md", "max_characters": 600}',
        help="JSON object containing typed tool arguments.",
    )
    return parser


def _events(events: Sequence[LifecycleEvent]) -> list[dict[str, Any]]:
    return [
        {
            "event": event.name,
            "task_id": event.task_id,
            "agent_id": event.agent_id,
            "state": event.state.value if event.state else None,
            "data": event.data,
        }
        for event in events
    ]


def _latest_task_id(runtime: Any) -> str | None:
    for event in reversed(runtime.components.events.snapshot()):
        if event.name == "task.created":
            return event.task_id
    return None


def _error_payload(runtime: Any, error: LabError) -> dict[str, Any]:
    task_id = _latest_task_id(runtime)
    return {
        "allowed": False,
        "error": error.as_dict(),
        "task_id": task_id,
        "final_state": (
            runtime.task_state(task_id).value if task_id is not None else None
        ),
        "state_history": (
            [item.to_state.value for item in runtime.state_history(task_id)]
            if task_id is not None
            else []
        ),
    }


def _parse_arguments(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValidationError(
            "--arguments must be valid JSON",
            details={"position": error.pos},
        ) from error
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValidationError("--arguments must decode to a JSON object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = build_stage1_runtime()
    for agent in stage3_agents():
        runtime.register_agent(agent)
    runtime.start()
    try:
        if args.demo:
            allowed = runtime.run_tool(
                agent_id="technical-explainer",
                tool_name="project_context_read",
                arguments={"relative_path": "README.md", "max_characters": 600},
            )
            try:
                runtime.run_tool(
                    agent_id="risk-analyst",
                    tool_name="project_context_read",
                    arguments={"relative_path": "README.md"},
                )
            except ToolPermissionDeniedError as denied_error:
                denied = _error_payload(runtime, denied_error)
            else:
                raise ValidationError(
                    "default-deny demonstration unexpectedly permitted the request"
                )
            payload = {
                "stage": 5,
                "purpose": "validated, permissioned, bounded local tool execution",
                "permitted_request": {"allowed": True, "result": allowed.as_dict()},
                "denied_request": denied,
                "lifecycle_events": _events(runtime.components.events.snapshot()),
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        arguments = _parse_arguments(args.arguments)
        try:
            result = runtime.run_tool(
                agent_id=args.agent,
                tool_name=args.tool,
                arguments=arguments,
            )
        except LabError as error:
            print(json.dumps(_error_payload(runtime, error), indent=2, sort_keys=True))
            return 2
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        return 0
    except LabError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 1
    finally:
        runtime.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
