"""Side-effect-free deterministic trace replay and cross-run comparison."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Protocol, Sequence

from ..models import utc_now
from .hashing import (
    GENESIS_HASH,
    compute_step_hash,
    hash_payload,
    semantic_hash,
    stable_step_id,
)
from .models import (
    DeterminismClass,
    ReplayOutcome,
    ReplayReport,
    ReplayStepResult,
    TraceComparison,
    TraceComparisonItem,
    TraceRun,
    TraceStep,
)


class ReplayTraceStore(Protocol):
    def load_run(self, run_id: str) -> TraceRun: ...

    def steps(self, run_id: str) -> Sequence[TraceStep]: ...

    def save_replay(self, report: ReplayReport) -> None: ...


class TraceReplayEngine:
    """Verify a trace chain and replay deterministic reducers only."""

    def __init__(self, store: ReplayTraceStore) -> None:
        self._store = store

    def replay(self, run_id: str) -> ReplayReport:
        started = utc_now()
        run = self._store.load_run(run_id)
        steps = tuple(self._store.steps(run_id))
        previous_hash = GENESIS_HASH
        current_state: str | None = None
        state_sequence = -1
        results: list[ReplayStepResult] = []
        integrity_valid = True

        for step in steps:
            valid, reason = self._verify_step(step, previous_hash)
            if valid and step.event_name == "task.state.changed":
                output = step.output_data
                sequence = int(output.get("sequence", -1))
                expected_from = output.get("from_state")
                if sequence != state_sequence + 1:
                    valid = False
                    reason = "state transition sequence is not contiguous"
                elif expected_from != current_state:
                    valid = False
                    reason = "state transition source does not match reconstructed state"
                else:
                    state_sequence = sequence
                    current_state = str(output.get("to_state"))

            if not valid:
                integrity_valid = False
                outcome = ReplayOutcome.INTEGRITY_FAILED
            elif step.determinism is DeterminismClass.DETERMINISTIC:
                outcome = ReplayOutcome.MATCHED
                reason = "canonical hashes and deterministic reducer matched"
            elif step.determinism is DeterminismClass.SIDE_EFFECTING:
                outcome = ReplayOutcome.SKIPPED_SIDE_EFFECT
                reason = "side-effecting operation was not re-executed"
            else:
                outcome = ReplayOutcome.OBSERVED_ONLY
                reason = "nondeterministic or environmental evidence was integrity-checked only"

            results.append(
                ReplayStepResult(
                    ordinal=step.ordinal,
                    step_id=step.step_id,
                    event_name=step.event_name,
                    determinism=step.determinism,
                    outcome=outcome,
                    reason=reason,
                )
            )
            previous_hash = step.step_hash

        if run.final_chain_hash is not None and previous_hash != run.final_chain_hash:
            integrity_valid = False
        finished = utc_now()
        report = ReplayReport(
            replay_id=str(uuid.uuid4()),
            source_run_id=run_id,
            started_at=started,
            finished_at=finished,
            status="matched" if integrity_valid else "integrity_failed",
            integrity_valid=integrity_valid,
            reconstructed_state=current_state,
            steps=tuple(results),
        )
        self._store.save_replay(report)
        return report

    @staticmethod
    def _verify_step(step: TraceStep, previous_hash: str) -> tuple[bool, str]:
        if step.previous_hash != previous_hash:
            return False, "trace hash chain is discontinuous"
        if step.step_id != stable_step_id(step.run_id, step.ordinal, step.event_name):
            return False, "step ID does not match the stable run/ordinal identity"
        if step.input_hash != hash_payload(step.input_data):
            return False, "input payload hash mismatch"
        if step.output_hash != hash_payload(step.output_data):
            return False, "output payload hash mismatch"
        if step.semantic_hash != semantic_hash(step.event_name, step.input_data, step.output_data):
            return False, "semantic payload hash mismatch"
        computed = compute_step_hash(
            run_id=step.run_id,
            ordinal=step.ordinal,
            step_id=step.step_id,
            recorded_at_utc=step.recorded_at.isoformat(),
            actor=step.actor,
            component=step.component,
            event_name=step.event_name,
            determinism=step.determinism.value,
            input_hash=step.input_hash,
            output_hash=step.output_hash,
            semantic_digest=step.semantic_hash,
            state_from=step.state_from,
            state_to=step.state_to,
            model_id=step.model_id,
            configuration_hash=step.configuration_hash,
            failure=step.failure,
            previous_hash=step.previous_hash,
        )
        if step.step_hash != computed:
            return False, "step envelope hash mismatch"
        return True, "trace step verified"


def compare_traces(left: TraceRun, left_steps: Sequence[TraceStep], right: TraceRun, right_steps: Sequence[TraceStep]) -> TraceComparison:
    def indexed(steps: Sequence[TraceStep]) -> dict[tuple[str, int], TraceStep]:
        counts: dict[str, int] = defaultdict(int)
        result: dict[tuple[str, int], TraceStep] = {}
        for step in steps:
            counts[step.event_name] += 1
            result[(step.event_name, counts[step.event_name])] = step
        return result

    left_index = indexed(left_steps)
    right_index = indexed(right_steps)
    matches = divergences = observations = missing = 0
    items: list[TraceComparisonItem] = []
    for key in sorted(set(left_index) | set(right_index)):
        left_step = left_index.get(key)
        right_step = right_index.get(key)
        determinism = (
            left_step.determinism.value
            if left_step is not None
            else right_step.determinism.value
        )
        if left_step is None or right_step is None:
            status = "missing"
            missing += 1
        elif (
            left_step.determinism is not DeterminismClass.DETERMINISTIC
            or right_step.determinism is not DeterminismClass.DETERMINISTIC
        ):
            status = "observed_nondeterministic"
            observations += 1
        elif left_step.semantic_hash == right_step.semantic_hash:
            status = "matched"
            matches += 1
        else:
            status = "diverged"
            divergences += 1
        items.append(
            TraceComparisonItem(
                event_name=key[0],
                occurrence=key[1],
                determinism=determinism,
                status=status,
                left_step_id=left_step.step_id if left_step else None,
                right_step_id=right_step.step_id if right_step else None,
            )
        )
    return TraceComparison(
        left_run_id=left.run_id,
        right_run_id=right.run_id,
        model_match=left.model_id == right.model_id,
        configuration_match=left.configuration_hash == right.configuration_hash,
        deterministic_matches=matches,
        deterministic_divergences=divergences,
        nondeterministic_observations=observations,
        missing_steps=missing,
        items=tuple(items),
    )
