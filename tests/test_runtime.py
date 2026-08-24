import unittest

from runtime.engine import AgentRuntime, RuntimeComponents
from runtime.cancellation import CancellationToken
from runtime.errors import (
    PolicyDeniedError,
    RuntimeLifecycleError,
    TaskExecutionError,
    ValidationError,
)
from runtime.factory import build_stage1_runtime
from runtime.models import (
    Agent,
    InferenceRequest,
    InferenceResult,
    PolicyDecision,
    RuntimeStatus,
    Task,
    TaskState,
)


def demo_agent(agent_id: str = "agent-1") -> Agent:
    return Agent(
        agent_id=agent_id,
        name="Test Agent",
        objective="Exercise the Stage 1 runtime",
    )


class DenyPolicy:
    def evaluate(self, task: Task, agent: Agent) -> PolicyDecision:
        return PolicyDecision(allowed=False, reason="denied by test policy")


class ExplodingBackend:
    name = "exploding-test-backend"

    def start(self) -> None:
        return None

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        raise OSError("simulated component failure")

    def shutdown(self) -> None:
        return None


def replace_components(
    runtime: AgentRuntime,
    *,
    inference: object | None = None,
    policy: object | None = None,
) -> AgentRuntime:
    current = runtime.components
    return AgentRuntime(
        config=runtime.config,
        components=RuntimeComponents(
            agents=current.agents,
            inference=inference or current.inference,  # type: ignore[arg-type]
            scheduler=current.scheduler,
            router=current.router,
            policy=policy or current.policy,  # type: ignore[arg-type]
            checkpoints=current.checkpoints,
            metrics=current.metrics,
            events=current.events,
            state_machine=current.state_machine,
        ),
    )


class AgentRuntimeLifecycleTests(unittest.TestCase):
    def test_complete_stub_lifecycle_crosses_every_component_boundary(self) -> None:
        runtime = build_stage1_runtime()
        agent = demo_agent()

        runtime.start()
        runtime.register_agent(agent)
        task = runtime.create_task(agent=agent, objective="Run one task")
        result = runtime.execute_task(task=task, agent=agent)
        runtime.shutdown()

        self.assertEqual(runtime.status, RuntimeStatus.STOPPED)
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(result.model_id, "stage-1-stub-model")
        self.assertEqual(result.backend_name, "stage-1-stub-backend")
        self.assertEqual(result.metadata["real_llm_calls"], 0)
        self.assertIn("STUB (no LLM inference): Run one task", result.output)

        event_names = [event.name for event in runtime.components.metrics.snapshot()]
        self.assertEqual(
            event_names,
            [
                "runtime.started",
                "agent.registered",
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
                "runtime.stopped",
            ],
        )

        checkpoint_store = runtime.components.checkpoints
        phases = [
            checkpoint.phase
            for checkpoint in checkpoint_store.for_task(task.task_id)  # type: ignore[attr-defined]
        ]
        self.assertEqual(
            phases,
            ["created", "planning", "executing", "validating", "completed"],
        )

    def test_create_task_requires_started_runtime(self) -> None:
        runtime = build_stage1_runtime()
        agent = demo_agent()
        runtime.register_agent(agent)

        with self.assertRaises(RuntimeLifecycleError):
            runtime.create_task(agent=agent, objective="Not yet")

    def test_start_rejects_double_start(self) -> None:
        runtime = build_stage1_runtime()
        runtime.start()
        self.addCleanup(runtime.shutdown)

        with self.assertRaises(RuntimeLifecycleError):
            runtime.start()

    def test_shutdown_is_idempotent(self) -> None:
        runtime = build_stage1_runtime()
        runtime.start()

        runtime.shutdown()
        runtime.shutdown()

        stopped_events = [
            event
            for event in runtime.components.metrics.snapshot()
            if event.name == "runtime.stopped"
        ]
        self.assertEqual(len(stopped_events), 1)

    def test_agent_mismatch_is_rejected_before_component_execution(self) -> None:
        runtime = build_stage1_runtime()
        owner = demo_agent("owner")
        other = demo_agent("other")
        runtime.start()
        self.addCleanup(runtime.shutdown)
        runtime.register_agent(owner)
        runtime.register_agent(other)
        task = runtime.create_task(agent=owner, objective="Owned task")

        with self.assertRaises(ValidationError):
            runtime.execute_task(task=task, agent=other)

    def test_policy_denial_is_structured_and_checkpointed(self) -> None:
        runtime = replace_components(build_stage1_runtime(), policy=DenyPolicy())
        agent = demo_agent()
        runtime.start()
        self.addCleanup(runtime.shutdown)
        runtime.register_agent(agent)
        task = runtime.create_task(agent=agent, objective="Denied task")

        with self.assertRaises(PolicyDeniedError) as caught:
            runtime.execute_task(task=task, agent=agent)

        self.assertEqual(caught.exception.as_dict()["code"], "policy_denied")
        self.assertEqual(runtime.components.checkpoints.latest(task.task_id).phase, "security_blocked")  # type: ignore[union-attr]
        self.assertEqual(runtime.task_state(task.task_id), TaskState.SECURITY_BLOCKED)

    def test_unexpected_component_failure_is_wrapped_and_recorded(self) -> None:
        runtime = replace_components(
            build_stage1_runtime(),
            inference=ExplodingBackend(),
        )
        agent = demo_agent()
        runtime.start()
        self.addCleanup(runtime.shutdown)
        runtime.register_agent(agent)
        task = runtime.create_task(agent=agent, objective="Fail predictably")

        with self.assertRaises(TaskExecutionError) as caught:
            runtime.execute_task(task=task, agent=agent)

        self.assertEqual(caught.exception.details["cause_type"], "OSError")
        self.assertEqual(runtime.components.checkpoints.latest(task.task_id).phase, "model_failed")  # type: ignore[union-attr]
        self.assertEqual(runtime.components.metrics.snapshot()[-1].name, "task.failed")
        self.assertEqual(runtime.task_state(task.task_id), TaskState.MODEL_FAILED)


if __name__ == "__main__":
    unittest.main()
