"""Validated resource-profile catalog loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import ConfigurationError
from ..models import InferenceProfile
from ..scheduler import WorkloadClass


@dataclass(frozen=True, slots=True)
class InferenceProfileCatalog:
    model_id: str
    layer_count: int
    profiles: tuple[InferenceProfile, ...]
    workload_order: dict[WorkloadClass, tuple[str, ...]]
    selection_notes: tuple[str, ...]

    def get(self, profile_id: str) -> InferenceProfile:
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        raise ConfigurationError(
            "inference profile is not registered",
            details={"profile_id": profile_id},
        )


def load_inference_profile_catalog(
    path: str | Path = "configs/inference-profiles.json",
) -> InferenceProfileCatalog:
    config_path = Path(path).resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ConfigurationError("unsupported inference-profile schema")
        model = payload["model"]
        layer_count = int(model["layer_count"])
        profiles = tuple(
            InferenceProfile(
                profile_id=str(item["id"]),
                purpose=str(item["purpose"]),
                context_size=int(item["context_size"]),
                batch_size=int(item["batch_size"]),
                ubatch_size=int(item["ubatch_size"]),
                threads=int(item["threads"]),
                threads_batch=int(item["threads_batch"]),
                gpu_layers=int(item["gpu_layers"]),
                flash_attention=str(item["flash_attention"]),
                devices=str(item.get("devices", "auto")),
            )
            for item in payload["profiles"]
        )
        ids = [profile.profile_id for profile in profiles]
        if not profiles or len(ids) != len(set(ids)):
            raise ConfigurationError("inference profile IDs must be non-empty and unique")
        if any(profile.gpu_layers > layer_count for profile in profiles):
            raise ConfigurationError("profile GPU layers exceed the declared model")
        order = {
            workload: tuple(str(value) for value in payload["workload_order"][workload.value])
            for workload in WorkloadClass
        }
        for workload, profile_ids in order.items():
            if set(profile_ids) != set(ids) or len(profile_ids) != len(ids):
                raise ConfigurationError(
                    "each workload order must contain every profile exactly once",
                    details={"workload": workload.value},
                )
        notes = tuple(str(note) for note in payload.get("selection_notes", []))
        return InferenceProfileCatalog(
            model_id=str(model["id"]),
            layer_count=layer_count,
            profiles=profiles,
            workload_order=order,
            selection_notes=notes,
        )
    except ConfigurationError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "could not load inference-profile configuration",
            details={"path": str(config_path), "cause_type": type(error).__name__},
        ) from error
