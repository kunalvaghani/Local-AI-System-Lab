"""Validated, inspectable Stage 4 task state machine."""

from __future__ import annotations

from threading import RLock

from .errors import IllegalStateTransitionError, TaskNotFoundError
from .models import StateTransition, TaskState


LEGAL_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.CREATED: frozenset(
        {
            TaskState.PLANNING,
            TaskState.CANCELLED,
        }
    ),
    TaskState.PLANNING: frozenset(
        {
            TaskState.RECOVERING,
            TaskState.WAITING_FOR_TOOL,
            TaskState.EXECUTING,
            TaskState.MODEL_FAILED,
            TaskState.TOOL_FAILED,
            TaskState.TIMEOUT,
            TaskState.INVALID_OUTPUT,
            TaskState.OUT_OF_MEMORY,
            TaskState.SECURITY_BLOCKED,
            TaskState.CONTEXT_OVERFLOW,
            TaskState.RESOURCE_BLOCKED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.RECOVERING: frozenset(
        {
            TaskState.PLANNING,
            TaskState.CANCELLED,
            TaskState.MODEL_FAILED,
        }
    ),
    TaskState.WAITING_FOR_TOOL: frozenset(
        {
            TaskState.PLANNING,
            TaskState.EXECUTING,
            TaskState.VALIDATING,
            TaskState.TOOL_FAILED,
            TaskState.TIMEOUT,
            TaskState.INVALID_OUTPUT,
            TaskState.SECURITY_BLOCKED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.EXECUTING: frozenset(
        {
            TaskState.VALIDATING,
            TaskState.MODEL_FAILED,
            TaskState.TIMEOUT,
            TaskState.OUT_OF_MEMORY,
            TaskState.CONTEXT_OVERFLOW,
            TaskState.CANCELLED,
        }
    ),
    TaskState.VALIDATING: frozenset(
        {
            TaskState.COMPLETED,
            TaskState.INVALID_OUTPUT,
            TaskState.TIMEOUT,
            TaskState.CANCELLED,
        }
    ),
    TaskState.COMPLETED: frozenset(),
    TaskState.MODEL_FAILED: frozenset(),
    TaskState.TOOL_FAILED: frozenset(),
    TaskState.TIMEOUT: frozenset(),
    TaskState.INVALID_OUTPUT: frozenset(),
    TaskState.OUT_OF_MEMORY: frozenset(),
    TaskState.SECURITY_BLOCKED: frozenset(),
    TaskState.CONTEXT_OVERFLOW: frozenset(),
    TaskState.RESOURCE_BLOCKED: frozenset(),
    TaskState.CANCELLED: frozenset(),
}


TERMINAL_STATES = frozenset(
    state for state, allowed in LEGAL_TRANSITIONS.items() if not allowed
)


class ExecutionStateMachine:
    """Stores ordered state histories and rejects every undeclared transition."""

    def __init__(self) -> None:
        self._histories: dict[str, list[StateTransition]] = {}
        self._lock = RLock()

    def initialize(
        self,
        task_id: str,
        *,
        reason: str = "task created by runtime",
    ) -> StateTransition:
        with self._lock:
            if task_id in self._histories:
                current = self._histories[task_id][-1].to_state
                raise IllegalStateTransitionError(
                    "task state machine is already initialized",
                    details={
                        "task_id": task_id,
                        "current_state": current.value,
                        "requested_state": TaskState.CREATED.value,
                    },
                )
            transition = StateTransition(
                sequence=0,
                from_state=None,
                to_state=TaskState.CREATED,
                reason=reason,
            )
            self._histories[task_id] = [transition]
            return transition

    def transition(
        self,
        task_id: str,
        to_state: TaskState,
        *,
        reason: str,
    ) -> StateTransition:
        with self._lock:
            history = self._require_history(task_id)
            current = history[-1].to_state
            allowed = LEGAL_TRANSITIONS[current]
            if to_state not in allowed:
                raise IllegalStateTransitionError(
                    "task state transition is not legal",
                    details={
                        "task_id": task_id,
                        "current_state": current.value,
                        "requested_state": to_state.value,
                        "allowed_states": sorted(state.value for state in allowed),
                    },
                )
            transition = StateTransition(
                sequence=len(history),
                from_state=current,
                to_state=to_state,
                reason=reason,
            )
            history.append(transition)
            return transition

    def current(self, task_id: str) -> TaskState:
        with self._lock:
            return self._require_history(task_id)[-1].to_state

    def history(self, task_id: str) -> tuple[StateTransition, ...]:
        with self._lock:
            return tuple(self._require_history(task_id))

    @staticmethod
    def is_terminal(state: TaskState) -> bool:
        return state in TERMINAL_STATES

    def _require_history(self, task_id: str) -> list[StateTransition]:
        try:
            return self._histories[task_id]
        except KeyError as error:
            raise TaskNotFoundError(
                "task state machine is not initialized",
                details={"task_id": task_id},
            ) from error
