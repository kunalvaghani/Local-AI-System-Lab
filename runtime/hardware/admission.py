"""Memory-aware admission policy and runtime gate."""

from __future__ import annotations

from dataclasses import replace

from ..scheduler import SchedulingOptions, WorkloadClass
from .config import AdmissionConfig
from .estimator import ConservativeMemoryEstimator
from .models import (
    AdmissionAction,
    AdmissionDecision,
    AdmissionRequest,
    Confidence,
    HardwareSnapshot,
    ModelMemoryProfile,
)
from .profiler import LocalHardwareProfiler


class AdmissionPolicy:
    """Select one inspectable action while retaining safety reserves."""

    def __init__(self, estimator: ConservativeMemoryEstimator) -> None:
        self.estimator = estimator

    def evaluate(
        self,
        request: AdmissionRequest,
        hardware: HardwareSnapshot,
    ) -> AdmissionDecision:
        estimate = self.estimator.estimate(request)
        config = self.estimator.config
        ram = hardware.ram.available_mib
        gpu = hardware.gpu
        free_vram = gpu.free_vram_mib if gpu is not None else None
        constraints = tuple(hardware.warnings)

        def decision(
            action: AdmissionAction,
            reason: str,
            *,
            context: int | None = None,
            gpu_layers: int | None = None,
            fallback: str | None = None,
            confidence: Confidence | None = None,
        ) -> AdmissionDecision:
            return AdmissionDecision(
                action=action,
                reason=reason,
                estimate=estimate,
                host_reserve_mib=config.host_reserve_mib,
                vram_reserve_mib=config.vram_reserve_mib,
                available_ram_mib=ram,
                free_vram_mib=free_vram,
                recommended_context_tokens=context,
                recommended_gpu_layers=gpu_layers,
                fallback_model_id=fallback,
                confidence=confidence or estimate.confidence,
                constraints=constraints,
            )

        if ram is None:
            return decision(
                AdmissionAction.REJECT_UNSAFE,
                "live available RAM is unknown, so safe admission cannot be established",
                confidence=Confidence.UNAVAILABLE,
            )

        host_required = estimate.predicted_host_ram_mib + config.host_reserve_mib
        if ram < host_required:
            context = self._context_that_fits_host(request, ram)
            if request.allow_context_reduction and context is not None:
                return decision(
                    AdmissionAction.REDUCE_CONTEXT,
                    "available RAM cannot preserve the configured host reserve",
                    context=context,
                    confidence=Confidence.LOW,
                )
            fallback = self._fitting_fallback(request, hardware)
            if fallback is not None:
                return decision(
                    AdmissionAction.FALLBACK,
                    "configured model exceeds available RAM but the declared fallback fits",
                    fallback=fallback.model_id,
                    confidence=Confidence.LOW,
                )
            return decision(
                AdmissionAction.REJECT_UNSAFE,
                "configured model plus host reserve exceeds available RAM",
            )

        if request.gpu_layers == 0:
            return decision(
                AdmissionAction.ACCEPT,
                "host estimate and reserve fit; this request uses no GPU offload",
            )

        if gpu is None:
            if request.allow_gpu_reduction:
                return decision(
                    AdmissionAction.REDUCE_GPU_OFFLOAD,
                    "GPU telemetry is unavailable; use zero GPU layers for a host-safe run",
                    gpu_layers=0,
                    confidence=Confidence.LOW,
                )
            fallback = self._fitting_fallback(request, hardware)
            if fallback is not None:
                return decision(
                    AdmissionAction.FALLBACK,
                    "GPU offload is unavailable but the declared fallback fits",
                    fallback=fallback.model_id,
                    confidence=Confidence.LOW,
                )
            return decision(
                AdmissionAction.REJECT_UNSAFE,
                "GPU offload was requested but GPU capacity cannot be established",
                confidence=Confidence.UNAVAILABLE,
            )

        vram_required = estimate.predicted_vram_mib + config.vram_reserve_mib
        if gpu.free_vram_mib >= vram_required:
            return decision(
                AdmissionAction.ACCEPT,
                "predicted host and GPU memory fit with configured safety reserves",
            )

        total_can_fit = gpu.total_vram_mib >= vram_required
        if total_can_fit and request.workload is WorkloadClass.BACKGROUND:
            return decision(
                AdmissionAction.QUEUE,
                "total VRAM can fit, but current pressure leaves insufficient free VRAM",
            )

        if request.allow_context_reduction:
            context = self._context_that_fits_vram(request, gpu.free_vram_mib)
            if context is not None:
                return decision(
                    AdmissionAction.REDUCE_CONTEXT,
                    "a shorter context can preserve the VRAM reserve under current pressure",
                    context=context,
                    confidence=Confidence.LOW,
                )

        if request.allow_gpu_reduction:
            gpu_layers = self._gpu_layers_that_fit(request, gpu.free_vram_mib)
            if gpu_layers is not None:
                return decision(
                    AdmissionAction.REDUCE_GPU_OFFLOAD,
                    "fewer GPU layers can preserve the VRAM reserve under current pressure",
                    gpu_layers=gpu_layers,
                    confidence=Confidence.LOW,
                )

        fallback = self._fitting_fallback(request, hardware)
        if fallback is not None:
            return decision(
                AdmissionAction.FALLBACK,
                "configured model does not fit current memory, but the declared fallback does",
                fallback=fallback.model_id,
                confidence=Confidence.LOW,
            )
        if total_can_fit:
            return decision(
                AdmissionAction.QUEUE,
                "capacity is sufficient after pressure clears; no safe reduction is allowed",
            )
        return decision(
            AdmissionAction.REJECT_UNSAFE,
            "model and reserves exceed capacity with no allowed safe adaptation",
        )

    def _context_that_fits_host(
        self, request: AdmissionRequest, available_ram_mib: float
    ) -> int | None:
        c = self.estimator.config
        fixed = (
            request.model.file_size_mib * c.host_weight_multiplier
            + c.host_fixed_overhead_mib
            + c.host_reserve_mib
        )
        if c.host_context_mib_per_token == 0:
            return None
        return self._valid_reduced_context(
            request, int((available_ram_mib - fixed) / c.host_context_mib_per_token)
        )

    def _context_that_fits_vram(
        self, request: AdmissionRequest, free_vram_mib: float
    ) -> int | None:
        c = self.estimator.config
        fraction = request.gpu_layers / request.model.layer_count
        fixed = (
            request.model.file_size_mib * c.vram_weight_multiplier * fraction
            + c.vram_fixed_overhead_mib
            + c.vram_reserve_mib
        )
        if c.vram_context_mib_per_token == 0:
            return None
        return self._valid_reduced_context(
            request, int((free_vram_mib - fixed) / c.vram_context_mib_per_token)
        )

    def _valid_reduced_context(
        self, request: AdmissionRequest, tokens: int
    ) -> int | None:
        minimum = self.estimator.config.minimum_context_tokens
        tokens = min(tokens, request.context_tokens - 1)
        return max(minimum, tokens) if tokens >= minimum else None

    def _gpu_layers_that_fit(
        self, request: AdmissionRequest, free_vram_mib: float
    ) -> int | None:
        c = self.estimator.config
        available_for_weights = (
            free_vram_mib
            - c.vram_reserve_mib
            - request.context_tokens * c.vram_context_mib_per_token
            - c.vram_fixed_overhead_mib
        )
        per_layer = (
            request.model.file_size_mib
            * c.vram_weight_multiplier
            / request.model.layer_count
        )
        layers = max(0, int(available_for_weights / per_layer))
        return layers if layers < request.gpu_layers else None

    def _fitting_fallback(
        self, request: AdmissionRequest, hardware: HardwareSnapshot
    ) -> ModelMemoryProfile | None:
        fallback = request.fallback_model
        if fallback is None or hardware.ram.available_mib is None:
            return None
        fallback_request = replace(
            request,
            model=fallback,
            context_tokens=min(request.context_tokens, fallback.baseline_context_tokens),
            gpu_layers=min(request.gpu_layers, fallback.baseline_gpu_layers),
            fallback_model=None,
        )
        estimate = self.estimator.estimate(fallback_request)
        c = self.estimator.config
        if hardware.ram.available_mib < estimate.predicted_host_ram_mib + c.host_reserve_mib:
            return None
        if fallback_request.gpu_layers and (
            hardware.gpu is None
            or hardware.gpu.free_vram_mib < estimate.predicted_vram_mib + c.vram_reserve_mib
        ):
            return None
        return fallback


class MemoryAwareAdmissionGate:
    """Profile immediately before execution and evaluate the configured model."""

    def __init__(
        self,
        config: AdmissionConfig,
        profiler: LocalHardwareProfiler | None = None,
    ) -> None:
        self.config = config
        self.profiler = profiler or LocalHardwareProfiler()
        self.estimator = ConservativeMemoryEstimator(config.estimator)
        self.policy = AdmissionPolicy(self.estimator)
        self.last_snapshot: HardwareSnapshot | None = None
        self.last_decision: AdmissionDecision | None = None

    def evaluate(
        self, task: object, scheduling: SchedulingOptions
    ) -> AdmissionDecision:
        snapshot = self.profiler.snapshot()
        request = AdmissionRequest(
            model=self.config.model,
            context_tokens=self.config.model.baseline_context_tokens,
            gpu_layers=self.config.model.baseline_gpu_layers,
            workload=scheduling.workload,
        )
        decision = self.policy.evaluate(request, snapshot)
        self.last_snapshot = snapshot
        self.last_decision = decision
        return decision
