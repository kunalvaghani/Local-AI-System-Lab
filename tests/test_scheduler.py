import time
import unittest
from dataclasses import replace
from threading import Event, Lock

from runtime.agents import TECHNICAL_EXPLAINER
from runtime.cancellation import CancellationToken
from runtime.engine import AgentRuntime
from runtime.errors import (
    InferenceCancelledError,
    SchedulerCancelledError,
    TaskTimeoutError,
    ValidationError,
)
from runtime.factory import build_stage1_runtime
from runtime.models import InferenceRequest, InferenceResult, Task, TaskState
from runtime.scheduler import (
    QueuedScheduler,
    SchedulerPolicy,
    SchedulerRequestStatus,
    SchedulingOptions,
    WorkloadClass,
)


def task(task_id: str) -> Task:
    created = Task.create(agent_id="scheduler-test", objective=f"Run {task_id}")
    return replace(created, task_id=task_id)


def value(label: str) -> InferenceResult:
    return InferenceResult(
        text=label,
        model_id="controlled-model",
        backend_name="controlled-scheduler-test",
    )


class SchedulerOrderingTests(unittest.TestCase):
    def _ordered_run(self, policy: SchedulerPolicy) -> tuple[list[str], object]:
        scheduler = QueuedScheduler(policy=policy, max_workers=1)
        scheduler.start()
        self.addCleanup(scheduler.shutdown)
        blocker_started = Event()
        release = Event()

        def blocker(cancellation: CancellationToken) -> InferenceResult:
            blocker_started.set()
            release.wait(1)
            return value("blocker")

        first = scheduler.submit(
            task("blocker"),
            blocker,
            SchedulingOptions(timeout_ms=None),
        )
        self.assertTrue(blocker_started.wait(0.5))
        background = scheduler.submit(
            task("background"),
            lambda cancellation: value("background"),
            SchedulingOptions(
                workload=WorkloadClass.BACKGROUND,
                timeout_ms=1_000,
            ),
        )
        interactive = scheduler.submit(
            task("interactive"),
            lambda cancellation: value("interactive"),
            SchedulingOptions(
                workload=WorkloadClass.INTERACTIVE,
                timeout_ms=1_000,
            ),
        )
        release.set()
        for handle in (first, background, interactive):
            handle.result(1)
        metrics = scheduler.snapshot()
        return list(metrics.execution_order), metrics

    def test_fifo_preserves_submission_order(self) -> None:
        order, metrics = self._ordered_run(SchedulerPolicy.FIFO)
        self.assertEqual(order, ["blocker", "background", "interactive"])
        self.assertEqual(metrics.completed, 3)  # type: ignore[attr-defined]

    def test_priority_runs_interactive_before_queued_background(self) -> None:
        order, metrics = self._ordered_run(SchedulerPolicy.PRIORITY)
        self.assertEqual(order, ["blocker", "interactive", "background"])
        self.assertEqual(metrics.peak_queue_depth, 2)  # type: ignore[attr-defined]

    def test_equal_priority_requests_keep_stable_sequence_order(self) -> None:
        scheduler = QueuedScheduler(policy=SchedulerPolicy.PRIORITY, max_workers=1)
        scheduler.start()
        self.addCleanup(scheduler.shutdown)
        started = Event()
        release = Event()

        def blocker(cancellation: CancellationToken) -> InferenceResult:
            started.set()
            release.wait(1)
            return value("blocker")

        handles = [
            scheduler.submit(
                task("blocker"), blocker, SchedulingOptions(timeout_ms=None)
            )
        ]
        self.assertTrue(started.wait(0.5))
        handles.append(
            scheduler.submit(
                task("equal-first"),
                lambda cancellation: value("first"),
                SchedulingOptions(priority=70),
            )
        )
        handles.append(
            scheduler.submit(
                task("equal-second"),
                lambda cancellation: value("second"),
                SchedulingOptions(priority=70),
            )
        )
        release.set()
        for handle in handles:
            handle.result(1)
        self.assertEqual(
            scheduler.snapshot().execution_order,
            ("blocker", "equal-first", "equal-second"),
        )

    def test_starvation_threshold_promotes_old_background_work(self) -> None:
        scheduler = QueuedScheduler(
            policy=SchedulerPolicy.PRIORITY,
            max_workers=1,
            starvation_threshold_ms=25,
        )
        scheduler.start()
        self.addCleanup(scheduler.shutdown)
        started = Event()
        release = Event()

        def blocker(cancellation: CancellationToken) -> InferenceResult:
            started.set()
            release.wait(1)
            return value("blocker")

        first = scheduler.submit(
            task("blocker"), blocker, SchedulingOptions(timeout_ms=None)
        )
        self.assertTrue(started.wait(0.5))
        background = scheduler.submit(
            task("aged-background"),
            lambda cancellation: value("aged-background"),
            SchedulingOptions(workload=WorkloadClass.BACKGROUND, timeout_ms=500),
        )
        time.sleep(0.035)
        interactive = scheduler.submit(
            task("new-interactive"),
            lambda cancellation: value("new-interactive"),
            SchedulingOptions(workload=WorkloadClass.INTERACTIVE, timeout_ms=500),
        )
        release.set()
        for handle in (first, background, interactive):
            handle.result(1)

        metrics = scheduler.snapshot()
        self.assertEqual(
            metrics.execution_order,
            ("blocker", "aged-background", "new-interactive"),
        )
        self.assertEqual(metrics.starvation_promotions, 1)


class SchedulerControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = QueuedScheduler(max_workers=1)
        self.scheduler.start()
        self.addCleanup(self.scheduler.shutdown)

    def test_invalid_scheduler_options_are_rejected_structurally(self) -> None:
        with self.assertRaises(ValidationError):
            SchedulingOptions(priority=True)
        with self.assertRaises(ValidationError):
            SchedulingOptions(timeout_ms=0)
        with self.assertRaises(ValidationError):
            QueuedScheduler(max_workers=0)

    def _block_worker(self) -> tuple[object, Event]:
        started = Event()
        release = Event()

        def blocker(cancellation: CancellationToken) -> InferenceResult:
            started.set()
            release.wait(1)
            return value("blocker")

        handle = self.scheduler.submit(
            task("blocker"), blocker, SchedulingOptions(timeout_ms=None)
        )
        self.assertTrue(started.wait(0.5))
        return handle, release

    def test_queued_request_can_be_cancelled_before_execution(self) -> None:
        blocker, release = self._block_worker()
        executed = Event()
        victim = self.scheduler.submit(
            task("cancelled"),
            lambda cancellation: (executed.set(), value("unexpected"))[1],
        )
        self.assertTrue(victim.cancel())
        with self.assertRaises(SchedulerCancelledError):
            victim.result(0.5)
        self.assertFalse(executed.is_set())
        self.assertEqual(
            self.scheduler.request_snapshot(victim.request_id).status,
            SchedulerRequestStatus.CANCELLED,
        )
        release.set()
        blocker.result(1)  # type: ignore[attr-defined]

    def test_queued_timeout_fires_while_worker_is_busy(self) -> None:
        blocker, release = self._block_worker()
        victim = self.scheduler.submit(
            task("queue-timeout"),
            lambda cancellation: value("unexpected"),
            SchedulingOptions(timeout_ms=25),
        )
        with self.assertRaises(TaskTimeoutError) as caught:
            victim.result(0.5)
        self.assertEqual(caught.exception.details["scope"], "queue")
        self.assertEqual(self.scheduler.snapshot().timed_out, 1)
        release.set()
        blocker.result(1)  # type: ignore[attr-defined]

    def test_active_timeout_signals_cooperative_operation(self) -> None:
        observed = Event()

        def slow(cancellation: CancellationToken) -> InferenceResult:
            cancellation.wait(1)
            if cancellation.is_cancelled:
                observed.set()
            return value("late")

        handle = self.scheduler.submit(
            task("active-timeout"),
            slow,
            SchedulingOptions(timeout_ms=25),
        )
        with self.assertRaises(TaskTimeoutError) as caught:
            handle.result(0.5)
        self.assertEqual(caught.exception.details["scope"], "queue_and_execution")
        self.assertTrue(observed.wait(0.2))

    def test_active_request_can_be_cancelled_cooperatively(self) -> None:
        started = Event()
        observed = Event()

        def active(cancellation: CancellationToken) -> InferenceResult:
            started.set()
            cancellation.wait(1)
            if cancellation.is_cancelled:
                observed.set()
            return value("late")

        handle = self.scheduler.submit(
            task("active-cancel"),
            active,
            SchedulingOptions(timeout_ms=None),
        )
        self.assertTrue(started.wait(0.5))
        self.assertTrue(handle.cancel())
        with self.assertRaises(SchedulerCancelledError):
            handle.result(0.5)
        self.assertTrue(observed.wait(0.2))
        self.assertEqual(self.scheduler.snapshot().cancelled, 1)

    def test_shutdown_cancels_running_and_queued_requests(self) -> None:
        scheduler = QueuedScheduler(max_workers=1)
        scheduler.start()
        active_started = Event()
        queued_executed = Event()

        def active(cancellation: CancellationToken) -> InferenceResult:
            active_started.set()
            cancellation.wait(1)
            return value("late")

        running = scheduler.submit(
            task("shutdown-running"),
            active,
            SchedulingOptions(timeout_ms=None),
        )
        self.assertTrue(active_started.wait(0.5))
        queued = scheduler.submit(
            task("shutdown-queued"),
            lambda cancellation: (queued_executed.set(), value("unexpected"))[1],
        )
        scheduler.shutdown()

        with self.assertRaises(SchedulerCancelledError):
            running.result(0.5)
        with self.assertRaises(SchedulerCancelledError):
            queued.result(0.5)
        self.assertFalse(queued_executed.is_set())

    def test_worker_concurrency_never_exceeds_configured_limit(self) -> None:
        scheduler = QueuedScheduler(max_workers=2)
        scheduler.start()
        self.addCleanup(scheduler.shutdown)
        lock = Lock()
        release = Event()
        two_running = Event()
        active = 0
        maximum = 0

        def controlled(cancellation: CancellationToken) -> InferenceResult:
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
                if active == 2:
                    two_running.set()
            release.wait(1)
            with lock:
                active -= 1
            return value("done")

        handles = [
            scheduler.submit(
                task(f"concurrent-{index}"),
                controlled,
                SchedulingOptions(timeout_ms=None),
            )
            for index in range(4)
        ]
        self.assertTrue(two_running.wait(0.5))
        self.assertEqual(scheduler.snapshot().running, 2)
        release.set()
        for handle in handles:
            handle.result(1)
        self.assertEqual(maximum, 2)


class SlowCancellationBackend:
    name = "slow-cancellation-backend"

    def start(self) -> None:
        return None

    def generate(
        self,
        request: InferenceRequest,
        cancellation: CancellationToken | None = None,
    ) -> InferenceResult:
        token = cancellation or CancellationToken()
        token.wait(1)
        if token.is_cancelled:
            raise InferenceCancelledError("controlled backend cancellation")
        return value("late")

    def shutdown(self) -> None:
        return None


class SchedulerRuntimeIntegrationTests(unittest.TestCase):
    def _runtime(self, backend: object | None = None) -> AgentRuntime:
        base = build_stage1_runtime()
        return AgentRuntime(
            config=base.config,
            components=replace(
                base.components,
                scheduler=QueuedScheduler(max_workers=1),
                inference=backend or base.components.inference,
            ),
        )

    def test_success_result_contains_queue_measurements(self) -> None:
        runtime = self._runtime()
        runtime.register_agent(TECHNICAL_EXPLAINER)
        runtime.start()
        self.addCleanup(runtime.shutdown)

        result = runtime.run(
            agent_id=TECHNICAL_EXPLAINER.agent_id,
            scheduling=SchedulingOptions(workload=WorkloadClass.INTERACTIVE),
        )

        scheduler = result.metadata["scheduler"]
        self.assertEqual(scheduler["workload"], "interactive")
        self.assertEqual(scheduler["status"], "completed")
        self.assertIsNotNone(scheduler["queue_wait_ms"])

    def test_runtime_maps_scheduler_timeout_to_timeout_state(self) -> None:
        runtime = self._runtime(SlowCancellationBackend())
        runtime.register_agent(TECHNICAL_EXPLAINER)
        runtime.start()
        self.addCleanup(runtime.shutdown)

        with self.assertRaises(TaskTimeoutError):
            runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                scheduling=SchedulingOptions(timeout_ms=25),
            )

        task_event = next(
            event
            for event in runtime.components.events.snapshot()
            if event.name == "task.created"
        )
        self.assertEqual(runtime.task_state(task_event.task_id), TaskState.TIMEOUT)  # type: ignore[arg-type]

    def test_runtime_maps_pre_cancelled_request_to_cancelled_state(self) -> None:
        runtime = self._runtime()
        runtime.register_agent(TECHNICAL_EXPLAINER)
        runtime.start()
        self.addCleanup(runtime.shutdown)
        cancellation = CancellationToken()
        cancellation.cancel()

        with self.assertRaises(SchedulerCancelledError):
            runtime.run(
                agent_id=TECHNICAL_EXPLAINER.agent_id,
                scheduling=SchedulingOptions(cancellation=cancellation),
            )

        task_event = next(
            event
            for event in runtime.components.events.snapshot()
            if event.name == "task.created"
        )
        self.assertEqual(runtime.task_state(task_event.task_id), TaskState.CANCELLED)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
