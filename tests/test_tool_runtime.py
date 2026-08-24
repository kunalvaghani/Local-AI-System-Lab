import unittest

from runtime.agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from runtime.cancellation import CancellationToken
from runtime.errors import (
    DuplicateToolError,
    TaskTimeoutError,
    ToolArgumentValidationError,
    ToolCancelledError,
    ToolNotFoundError,
    ToolPathDeniedError,
    ToolPermissionDeniedError,
    ToolResultValidationError,
    ToolExecutionError,
)
from runtime.factory import build_stage1_runtime
from runtime.models import TaskState
from runtime.tools import (
    InMemoryToolRegistry,
    ThreadedToolExecutor,
    ToolDefinition,
    ToolPermissionMetadata,
    ToolRequest,
)


class SafeToolRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = build_stage1_runtime()
        self.runtime.register_agent(TECHNICAL_EXPLAINER)
        self.runtime.register_agent(RISK_ANALYST)
        self.runtime.start()
        self.addCleanup(self.runtime.shutdown)

    def _latest_task_id(self) -> str:
        event = next(
            event
            for event in reversed(self.runtime.components.events.snapshot())
            if event.name == "task.created"
        )
        assert event.task_id is not None
        return event.task_id

    def test_permitted_tool_returns_structured_result_and_success_history(self) -> None:
        result = self.runtime.run_tool(
            agent_id="technical-explainer",
            tool_name="project_context_read",
            arguments={"relative_path": "README.md", "max_characters": 80},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.agent_id, "technical-explainer")
        self.assertEqual(result.data["relative_path"], "README.md")
        self.assertLessEqual(result.data["characters_returned"], 80)
        self.assertEqual(
            [item.to_state for item in result.state_history],
            [
                TaskState.CREATED,
                TaskState.PLANNING,
                TaskState.WAITING_FOR_TOOL,
                TaskState.VALIDATING,
                TaskState.COMPLETED,
            ],
        )
        self.assertEqual(self.runtime.components.inference.call_count, 0)  # type: ignore[attr-defined]

    def test_missing_agent_grant_is_default_denied_and_security_blocked(self) -> None:
        with self.assertRaises(ToolPermissionDeniedError) as caught:
            self.runtime.run_tool(
                agent_id="risk-analyst",
                tool_name="project_context_read",
                arguments={"relative_path": "README.md"},
            )

        task_id = self._latest_task_id()
        self.assertEqual(caught.exception.details["decision"], "deny")
        self.assertEqual(self.runtime.task_state(task_id), TaskState.SECURITY_BLOCKED)

    def test_risk_agent_can_read_only_its_fixed_register_tool(self) -> None:
        result = self.runtime.run_tool(
            agent_id="risk-analyst",
            tool_name="risk_register_read",
            arguments={"max_characters": 120},
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data["relative_path"], "docs/risks.md")
        self.assertEqual(result.final_state, TaskState.COMPLETED)

    def test_path_escape_is_denied_and_security_blocked(self) -> None:
        with self.assertRaises(ToolPathDeniedError):
            self.runtime.run_tool(
                agent_id="technical-explainer",
                tool_name="project_context_read",
                arguments={"relative_path": "../outside.md"},
            )

        self.assertEqual(
            self.runtime.task_state(self._latest_task_id()),
            TaskState.SECURITY_BLOCKED,
        )

    def test_argument_validation_is_strict_and_tool_failed(self) -> None:
        with self.assertRaises(ToolArgumentValidationError) as caught:
            self.runtime.run_tool(
                agent_id="technical-explainer",
                tool_name="project_context_read",
                arguments={"relative_path": "README.md", "max_characters": "80"},
            )

        self.assertEqual(caught.exception.details["expected_type"], "integer")
        self.assertEqual(
            self.runtime.task_state(self._latest_task_id()),
            TaskState.TOOL_FAILED,
        )

    def test_missing_and_unknown_arguments_are_rejected(self) -> None:
        cases = (
            ({}, "argument"),
            ({"relative_path": "README.md", "extra": True}, "unknown_arguments"),
        )
        for arguments, detail_key in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ToolArgumentValidationError) as caught:
                    self.runtime.run_tool(
                        agent_id="technical-explainer",
                        tool_name="project_context_read",
                        arguments=arguments,
                    )
                self.assertIn(detail_key, caught.exception.details)

    def test_cancelled_request_enters_cancelled_terminal_state(self) -> None:
        cancellation = CancellationToken()
        cancellation.cancel()

        with self.assertRaises(ToolCancelledError):
            self.runtime.run_tool(
                agent_id="technical-explainer",
                tool_name="project_context_read",
                arguments={"relative_path": "README.md"},
                cancellation=cancellation,
            )

        self.assertEqual(
            self.runtime.task_state(self._latest_task_id()),
            TaskState.CANCELLED,
        )


def definition(name: str = "test_tool", timeout_ms: int = 100) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description="A controlled test tool.",
        arguments=(),
        permission=ToolPermissionMetadata(
            permissions=frozenset({"test.execute"}),
            read_only=True,
        ),
        timeout_ms=timeout_ms,
    )


def request(name: str = "test_tool") -> ToolRequest:
    return ToolRequest.create(
        task_id="task-1",
        agent_id="agent-1",
        tool_name=name,
    )


class ToolRegistryAndExecutorTests(unittest.TestCase):
    def test_registry_rejects_duplicate_and_missing_tools(self) -> None:
        registry = InMemoryToolRegistry()
        registry.register(definition(), lambda arguments, cancellation: {})
        with self.assertRaises(DuplicateToolError):
            registry.register(definition(), lambda arguments, cancellation: {})
        with self.assertRaises(ToolNotFoundError):
            registry.get("missing")

    def test_executor_enforces_timeout_and_signals_handler_cancellation(self) -> None:
        registry = InMemoryToolRegistry()
        observed = CancellationToken()

        def slow(arguments: dict[str, object], cancellation: CancellationToken) -> dict[str, object]:
            cancellation.wait(1)
            if cancellation.is_cancelled:
                observed.cancel()
            return {}

        registry.register(definition(timeout_ms=20), slow)
        with self.assertRaises(TaskTimeoutError):
            ThreadedToolExecutor().execute(registry.get("test_tool"), request())
        self.assertTrue(observed.wait(0.2))

    def test_executor_honors_external_cancellation(self) -> None:
        registry = InMemoryToolRegistry()
        registry.register(
            definition(),
            lambda arguments, cancellation: {},
        )
        cancellation = CancellationToken()
        cancellation.cancel()
        with self.assertRaises(ToolCancelledError):
            ThreadedToolExecutor().execute(
                registry.get("test_tool"), request(), cancellation
            )

    def test_executor_rejects_an_invalid_handler_result(self) -> None:
        registry = InMemoryToolRegistry()
        registry.register(
            definition(),
            lambda arguments, cancellation: "not a result",  # type: ignore[return-value]
        )
        with self.assertRaises(ToolResultValidationError):
            ThreadedToolExecutor().execute(registry.get("test_tool"), request())

    def test_executor_wraps_unexpected_handler_failure(self) -> None:
        registry = InMemoryToolRegistry()

        def broken(arguments: dict[str, object], cancellation: CancellationToken) -> dict[str, object]:
            raise RuntimeError("controlled failure")

        registry.register(definition(), broken)
        with self.assertRaises(ToolExecutionError) as caught:
            ThreadedToolExecutor().execute(registry.get("test_tool"), request())
        self.assertEqual(caught.exception.details["cause_type"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
