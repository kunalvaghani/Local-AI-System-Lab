import unittest

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.cancellation import CancellationToken
from runtime.engine import AgentRuntime, RuntimeComponents
from runtime.errors import (
    ContextOverflowError,
    IllegalStateTransitionError,
    InferenceCancelledError,
    InvalidOutputError,
    ModelOutOfMemoryError,
    TaskTimeoutError,
)
from runtime.factory import build_stage1_runtime
from runtime.models import InferenceRequest, InferenceResult, TaskState
from runtime.state_machine import ExecutionStateMachine, TERMINAL_STATES


class ExplicitStateMachineTests(unittest.TestCase):
    def test_success_path_is_ordered_and_deterministic(self) -> None:
        machine = ExecutionStateMachine()
        machine.initialize("task-1", reason="created")
        machine.transition("task-1", TaskState.PLANNING, reason="plan")
        machine.transition("task-1", TaskState.EXECUTING, reason="invoke")
        machine.transition("task-1", TaskState.VALIDATING, reason="validate")
        machine.transition("task-1", TaskState.COMPLETED, reason="accept")

        history = machine.history("task-1")
        self.assertEqual([item.sequence for item in history], list(range(5)))
        self.assertEqual(
            [item.to_state for item in history],
            [
                TaskState.CREATED,
                TaskState.PLANNING,
                TaskState.EXECUTING,
                TaskState.VALIDATING,
                TaskState.COMPLETED,
            ],
        )

    def test_illegal_transition_reports_current_requested_and_allowed(self) -> None:
        machine = ExecutionStateMachine()
        machine.initialize("task-1", reason="created")

        with self.assertRaises(IllegalStateTransitionError) as caught:
            machine.transition(
                "task-1",
                TaskState.COMPLETED,
                reason="skip required work",
            )

        self.assertEqual(caught.exception.details["current_state"], "created")
        self.assertEqual(caught.exception.details["requested_state"], "completed")
        self.assertEqual(
            caught.exception.details["allowed_states"],
            ["cancelled", "planning"],
        )

    def test_every_failure_state_is_terminal_and_rejects_reentry(self) -> None:
        scenarios = {
            TaskState.MODEL_FAILED: [TaskState.PLANNING, TaskState.EXECUTING],
            TaskState.TOOL_FAILED: [TaskState.PLANNING, TaskState.WAITING_FOR_TOOL],
            TaskState.TIMEOUT: [TaskState.PLANNING],
            TaskState.INVALID_OUTPUT: [TaskState.PLANNING],
            TaskState.OUT_OF_MEMORY: [TaskState.PLANNING, TaskState.EXECUTING],
            TaskState.SECURITY_BLOCKED: [TaskState.PLANNING],
            TaskState.CONTEXT_OVERFLOW: [TaskState.PLANNING, TaskState.EXECUTING],
            TaskState.RESOURCE_BLOCKED: [TaskState.PLANNING],
            TaskState.CANCELLED: [],
        }
        self.assertEqual(set(scenarios), set(TERMINAL_STATES) - {TaskState.COMPLETED})

        for index, (failure, path) in enumerate(scenarios.items()):
            with self.subTest(failure=failure):
                task_id = f"failure-{index}"
                machine = ExecutionStateMachine()
                machine.initialize(task_id, reason="created")
                for state in path:
                    machine.transition(task_id, state, reason=f"enter {state.value}")
                machine.transition(task_id, failure, reason="controlled failure")
                self.assertTrue(machine.is_terminal(machine.current(task_id)))
                with self.assertRaises(IllegalStateTransitionError):
                    machine.transition(task_id, TaskState.PLANNING, reason="retry")

    def test_waiting_for_tool_can_return_to_planning(self) -> None:
        machine = ExecutionStateMachine()
        machine.initialize("tool-task", reason="created")
        machine.transition("tool-task", TaskState.PLANNING, reason="plan")
        machine.transition(
            "tool-task",
            TaskState.WAITING_FOR_TOOL,
            reason="metadata declares a future tool",
        )
        machine.transition("tool-task", TaskState.PLANNING, reason="tool result available")

        self.assertEqual(machine.current("tool-task"), TaskState.PLANNING)


class FailureBackend:
    name = "controlled-failure-backend"

    def __init__(self, failure: Exception | None = None, *, output: str = "ok") -> None:
        self.failure = failure
        self.output = output

    def start(self) -> None:
        return None

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        if self.failure is not None:
            raise self.failure
        return InferenceResult(
            text=self.output,
            model_id=request.model_id,
            backend_name=self.name,
        )

    def shutdown(self) -> None:
        return None


def runtime_with_backend(backend: FailureBackend) -> AgentRuntime:
    base = build_stage1_runtime()
    current = base.components
    runtime = AgentRuntime(
        config=base.config,
        components=RuntimeComponents(
            agents=current.agents,
            inference=backend,  # type: ignore[arg-type]
            scheduler=current.scheduler,
            router=current.router,
            policy=current.policy,
            checkpoints=current.checkpoints,
            metrics=current.metrics,
            events=current.events,
            state_machine=current.state_machine,
        ),
    )
    runtime.register_agent(TECHNICAL_EXPLAINER)
    runtime.start()
    return runtime


class RuntimeFailureStateTests(unittest.TestCase):
    def _assert_failure_state(
        self,
        backend: FailureBackend,
        expected_exception: type[Exception],
        expected_state: TaskState,
    ) -> None:
        runtime = runtime_with_backend(backend)
        self.addCleanup(runtime.shutdown)

        with self.assertRaises(expected_exception):
            runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)

        task_event = next(
            event
            for event in runtime.components.events.snapshot()
            if event.name == "task.created"
        )
        self.assertIsNotNone(task_event.task_id)
        self.assertEqual(runtime.task_state(task_event.task_id), expected_state)  # type: ignore[arg-type]

    def test_runtime_maps_typed_failures_to_specific_terminal_states(self) -> None:
        cases = (
            (
                FailureBackend(ModelOutOfMemoryError("oom")),
                ModelOutOfMemoryError,
                TaskState.OUT_OF_MEMORY,
            ),
            (
                FailureBackend(ContextOverflowError("context")),
                ContextOverflowError,
                TaskState.CONTEXT_OVERFLOW,
            ),
            (
                FailureBackend(TaskTimeoutError("timeout")),
                TaskTimeoutError,
                TaskState.TIMEOUT,
            ),
            (
                FailureBackend(InferenceCancelledError("cancelled")),
                InferenceCancelledError,
                TaskState.CANCELLED,
            ),
            (
                FailureBackend(output="   "),
                InvalidOutputError,
                TaskState.INVALID_OUTPUT,
            ),
        )
        for backend, exception_type, state in cases:
            with self.subTest(state=state):
                self._assert_failure_state(backend, exception_type, state)


if __name__ == "__main__":
    unittest.main()
