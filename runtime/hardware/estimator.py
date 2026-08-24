"""Transparent, deliberately conservative memory estimation."""

from __future__ import annotations

from .config import CalibrationRecord, EstimatorConfig
from .models import (
    AdmissionRequest,
    CalibrationComparison,
    Confidence,
    MemoryEstimate,
)


class ConservativeMemoryEstimator:
    """Estimate working memory from inspectable coefficients, not hidden heuristics."""

    def __init__(self, config: EstimatorConfig) -> None:
        self.config = config

    def estimate(self, request: AdmissionRequest) -> MemoryEstimate:
        model = request.model
        offload_fraction = request.gpu_layers / model.layer_count
        host_weight = model.file_size_mib * self.config.host_weight_multiplier
        host_context = request.context_tokens * self.config.host_context_mib_per_token
        host_fixed = self.config.host_fixed_overhead_mib
        if request.gpu_layers:
            vram_weight = (
                model.file_size_mib
                * self.config.vram_weight_multiplier
                * offload_fraction
            )
            vram_context = (
                request.context_tokens * self.config.vram_context_mib_per_token
            )
            vram_fixed = self.config.vram_fixed_overhead_mib
        else:
            vram_weight = vram_context = vram_fixed = 0.0
        baseline = (
            request.context_tokens == model.baseline_context_tokens
            and request.gpu_layers == model.baseline_gpu_layers
        )
        return MemoryEstimate(
            model_id=model.model_id,
            context_tokens=request.context_tokens,
            gpu_layers=request.gpu_layers,
            predicted_host_ram_mib=round(host_weight + host_context + host_fixed, 3),
            predicted_vram_mib=round(vram_weight + vram_context + vram_fixed, 3),
            host_weight_component_mib=round(host_weight, 3),
            host_context_component_mib=round(host_context, 3),
            host_fixed_component_mib=round(host_fixed, 3),
            vram_weight_component_mib=round(vram_weight, 3),
            vram_context_component_mib=round(vram_context, 3),
            vram_fixed_component_mib=round(vram_fixed, 3),
            confidence=Confidence.MEDIUM if baseline else Confidence.LOW,
            assumptions=(
                "coefficients are calibrated to one Qwen Q4_K_M llama.cpp run",
                "host estimate remains conservative when GPU offload changes",
                "driver/runtime fragmentation and concurrent allocations are not predictable",
            ),
        )

    def compare_calibration(
        self,
        request: AdmissionRequest,
        observed: CalibrationRecord,
    ) -> CalibrationComparison:
        estimate = self.estimate(request)
        host_error = estimate.predicted_host_ram_mib - observed.observed_peak_child_ram_mib
        vram_error = estimate.predicted_vram_mib - observed.observed_vram_delta_mib
        return CalibrationComparison(
            predicted_host_ram_mib=estimate.predicted_host_ram_mib,
            observed_host_ram_mib=observed.observed_peak_child_ram_mib,
            host_error_mib=round(host_error, 3),
            host_error_percent=round(
                host_error / observed.observed_peak_child_ram_mib * 100, 3
            ),
            predicted_vram_mib=estimate.predicted_vram_mib,
            observed_vram_mib=observed.observed_vram_delta_mib,
            vram_error_mib=round(vram_error, 3),
            vram_error_percent=round(
                vram_error / observed.observed_vram_delta_mib * 100, 3
            ),
            source=observed.source,
        )
