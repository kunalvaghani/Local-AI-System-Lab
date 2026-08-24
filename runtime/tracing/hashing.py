"""Canonical hashing and trace-step classification."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from .models import DeterminismClass


GENESIS_HASH = "0" * 64

_VOLATILE_KEYS = frozenset(
    {
        "recorded_at_utc",
        "request_id",
        "task_id",
        "run_id",
        "attempt_id",
        "queue_wait_ms",
        "execution_ms",
        "elapsed_ms",
        "started_at_utc",
        "finished_at_utc",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def hash_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def semantic_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): semantic_payload(item)
            for key, item in sorted(value.items())
            if str(key) not in _VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [semantic_payload(item) for item in value]
    return value


def semantic_hash(event_name: str, input_data: dict[str, Any], output_data: dict[str, Any]) -> str:
    return hash_payload(
        {
            "event_name": event_name,
            "input": semantic_payload(input_data),
            "output": semantic_payload(output_data),
        }
    )


def stable_step_id(run_id: str, ordinal: int, event_name: str) -> str:
    return str(uuid.uuid5(uuid.UUID(run_id), f"{ordinal}:{event_name}"))


def classify_event(event_name: str) -> DeterminismClass:
    if event_name.startswith("model.") or event_name == "inference.output.persisted":
        return DeterminismClass.NONDETERMINISTIC
    if (
        event_name.startswith("tool.invocation")
        or event_name.startswith("tool.request")
        or event_name.startswith("tool.result.persisted")
        or event_name.startswith("tool.output.persisted")
        or event_name.startswith("tool.error.persisted")
    ):
        return DeterminismClass.SIDE_EFFECTING
    if event_name.startswith("scheduler.") or event_name.startswith("admission."):
        return DeterminismClass.OBSERVATIONAL
    if event_name.startswith("inference.profile"):
        return DeterminismClass.OBSERVATIONAL
    if event_name.startswith("recovery."):
        return DeterminismClass.OBSERVATIONAL
    return DeterminismClass.DETERMINISTIC


def actor_component(event_name: str) -> tuple[str, str]:
    prefix = event_name.split(".", 1)[0]
    mapping = {
        "task": ("agent-runtime", "state-machine"),
        "runtime": ("runtime", "lifecycle"),
        "agent": ("agent-runtime", "agent-registry"),
        "policy": ("policy-engine", "policy"),
        "tool": ("agent-runtime", "tool-runtime"),
        "route": ("model-router", "routing"),
        "compute_budget": ("budget-policy", "compute-budget"),
        "inference": ("inference-controller", "adaptive-inference"),
        "admission": ("admission-gate", "hardware-admission"),
        "scheduler": ("scheduler", "request-scheduler"),
        "model": ("inference-backend", "model-inference"),
        "output": ("agent-runtime", "output-validator"),
        "recovery": ("agent-runtime", "recovery"),
    }
    return mapping.get(prefix, (prefix, prefix))


def step_hash_payload(
    *,
    run_id: str,
    ordinal: int,
    step_id: str,
    recorded_at_utc: str,
    actor: str,
    component: str,
    event_name: str,
    determinism: str,
    input_hash: str,
    output_hash: str,
    semantic_digest: str,
    state_from: str | None,
    state_to: str | None,
    model_id: str | None,
    configuration_hash: str | None,
    failure: dict[str, Any] | None,
    previous_hash: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "ordinal": ordinal,
        "step_id": step_id,
        "recorded_at_utc": recorded_at_utc,
        "actor": actor,
        "component": component,
        "event_name": event_name,
        "determinism": determinism,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "semantic_hash": semantic_digest,
        "state_from": state_from,
        "state_to": state_to,
        "model_id": model_id,
        "configuration_hash": configuration_hash,
        "failure": failure,
        "previous_hash": previous_hash,
    }


def compute_step_hash(**values: Any) -> str:
    return hash_payload(step_hash_payload(**values))
