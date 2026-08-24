import unittest

from runtime.agents import RISK_ANALYST, TECHNICAL_EXPLAINER
from runtime.errors import AgentNotFoundError, DuplicateAgentError, TaskNotFoundError
from runtime.factory import build_stage1_runtime
from runtime.models import Task, TaskState


class SpecializedAgentRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = build_stage1_runtime()
        self.runtime.register_agent(TECHNICAL_EXPLAINER)
        self.runtime.register_agent(RISK_ANALYST)
        self.runtime.start()
        self.addCleanup(self.runtime.shutdown)

    def test_two_specialized_agents_execute_through_runtime(self) -> None:
        explanation = self.runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)
        risk = self.runtime.run(agent_id=RISK_ANALYST.agent_id)

        self.assertEqual(explanation.agent_id, "technical-explainer")
        self.assertEqual(risk.agent_id, "risk-analyst")
        self.assertEqual(explanation.final_state, TaskState.COMPLETED)
        self.assertEqual(risk.final_state, TaskState.COMPLETED)
        self.assertEqual(self.runtime.task_state(explanation.task_id), TaskState.COMPLETED)
        self.assertEqual(explanation.metadata["tool_capabilities"], ["project_context_read"])
        self.assertEqual(risk.metadata["tool_capabilities"], ["risk_register_read"])
        self.assertEqual(self.runtime.components.inference.call_count, 2)  # type: ignore[attr-defined]
        self.assertEqual(
            self.runtime.components.inference.last_request.system_prompt,  # type: ignore[attr-defined,union-attr]
            RISK_ANALYST.system_prompt,
        )

    def test_task_lifecycle_is_explicit_and_agent_scoped(self) -> None:
        result = self.runtime.run(agent_id=TECHNICAL_EXPLAINER.agent_id)

        events = self.runtime.components.events.snapshot(result.task_id)
        self.assertEqual(
            [event.name for event in events],
            [
                "task.created",
                "task.state.changed",
                "task.state.changed",
                "policy.evaluated",
                "route.selected",
                "task.state.changed",
                "scheduler.request.requested",
                "model.invocation.started",
                "model.invocation.completed",
                "scheduler.request.completed",
                "task.state.changed",
                "output.validation.completed",
                "task.state.changed",
                "task.completed",
            ],
        )
        self.assertTrue(all(event.agent_id == TECHNICAL_EXPLAINER.agent_id for event in events))
        self.assertEqual(
            [transition.to_state for transition in result.state_history],
            [
                TaskState.CREATED,
                TaskState.PLANNING,
                TaskState.EXECUTING,
                TaskState.VALIDATING,
                TaskState.COMPLETED,
            ],
        )

    def test_unknown_and_duplicate_agents_return_structured_errors(self) -> None:
        with self.assertRaises(AgentNotFoundError) as missing:
            self.runtime.run(agent_id="missing-agent")
        self.assertEqual(missing.exception.code, "agent_not_found")

        with self.assertRaises(DuplicateAgentError) as duplicate:
            self.runtime.register_agent(TECHNICAL_EXPLAINER)
        self.assertEqual(duplicate.exception.details["agent_id"], "technical-explainer")

    def test_runtime_rejects_a_task_it_did_not_create(self) -> None:
        external = Task.create(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            objective="Bypass task creation",
        )

        with self.assertRaises(TaskNotFoundError) as caught:
            self.runtime.execute_task(task=external, agent=TECHNICAL_EXPLAINER)

        self.assertEqual(getattr(caught.exception, "code", None), "task_not_found")


if __name__ == "__main__":
    unittest.main()
