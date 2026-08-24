"""Explainable workload-aware model routing over a validated local registry."""

from __future__ import annotations

from ..errors import ModelRoutingError
from ..models import Agent, RouteDecision, Task
from .config import ModelRegistry
from .models import (
    CandidateEvaluation,
    LatencyClass,
    RegisteredModel,
    RoutingContext,
    TaskComplexity,
)


class WorkloadModelRouter:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.last_decision: RouteDecision | None = None

    def route(self, task: Task, agent: Agent, context: RoutingContext) -> RouteDecision:
        task_type = self._task_type(task, agent)
        complexity = self._complexity(task, task_type)
        context_tokens = self._positive_int(task.input_data.get("context_length"), max(128, len(task.objective.split()) * 2))
        expected_output = self._positive_int(task.input_data.get("expected_output_tokens"), context.budget.max_generated_tokens)
        latency_requirement = self._positive_int(task.input_data.get("latency_requirement_ms"), context.scheduling.timeout_ms or context.budget.total_time_ms)
        evaluations: list[CandidateEvaluation] = []
        accepted: list[tuple[float, RegisteredModel]] = []

        for model in self.registry.models:
            failures: list[str] = []
            if not model.artifact_available:
                failures.append("artifact is not installed")
            if not model.backend_configured:
                failures.append("no runtime backend is configured")
            if task_type not in model.capabilities:
                failures.append(f"capability {task_type} is not declared")
            if context_tokens > model.max_context_tokens:
                failures.append(f"context {context_tokens} exceeds limit {model.max_context_tokens}")
            if expected_output > model.max_output_tokens:
                failures.append(f"expected output {expected_output} exceeds limit {model.max_output_tokens}")
            budget = context.budget
            if budget.max_ram_mib is not None and model.minimum_ram_mib > budget.max_ram_mib:
                failures.append("minimum model RAM exceeds task budget")
            if budget.max_vram_mib is not None and model.minimum_vram_mib > budget.max_vram_mib:
                failures.append("minimum model VRAM exceeds task budget")
            available_ram = context.hardware.ram.available_mib
            if available_ram is not None and model.minimum_ram_mib > available_ram:
                failures.append("minimum model RAM exceeds live availability")
            free_vram = context.hardware.gpu.free_vram_mib if context.hardware.gpu else 0.0
            if model.minimum_vram_mib > free_vram:
                failures.append("minimum model VRAM exceeds live availability")

            if failures:
                evaluations.append(CandidateEvaluation(model.model_id, False, None, tuple(failures)))
                continue

            score, reasons = self._score(model, context, complexity, latency_requirement)
            evaluations.append(CandidateEvaluation(model.model_id, True, score, reasons))
            accepted.append((score, model))

        if not accepted:
            raise ModelRoutingError(
                "no registered local model satisfies route constraints",
                details={
                    "task_type": task_type,
                    "complexity": complexity.value,
                    "candidates": [item.as_dict() for item in evaluations],
                },
            )
        score, selected = max(accepted, key=lambda item: (item[0], item[1].model_id))
        reason = (
            f"selected {selected.model_id} for {context.scheduling.workload.value} "
            f"{task_type}/{complexity.value}; score {score:.2f} was highest among safe available candidates"
        )
        decision = RouteDecision(
            model_id=selected.model_id,
            reason=reason,
            evidence={
                "task_type": task_type,
                "complexity": complexity.value,
                "context_length": context_tokens,
                "expected_output_tokens": expected_output,
                "latency_requirement_ms": latency_requirement,
                "workload": context.scheduling.workload.value,
                "queue_depth": context.queue_depth,
                "budget": context.budget.as_dict(),
                "hardware": context.hardware.as_dict(),
                "selected_model": selected.as_dict(),
                "candidates": [item.as_dict() for item in evaluations],
            },
        )
        self.last_decision = decision
        return decision

    @staticmethod
    def _positive_int(value: object, default: int) -> int:
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
        return default

    @staticmethod
    def _task_type(task: Task, agent: Agent) -> str:
        requested = task.input_data.get("task_type")
        if isinstance(requested, str) and requested.strip():
            return requested.strip().lower()
        if "risk_analysis" in agent.capabilities or "risk" in agent.agent_id:
            return "risk_analysis"
        if "technical_explanation" in agent.capabilities or "explainer" in agent.agent_id:
            return "explanation"
        return "general"

    @staticmethod
    def _complexity(task: Task, task_type: str) -> TaskComplexity:
        requested = task.input_data.get("complexity")
        if isinstance(requested, str):
            try:
                return TaskComplexity(requested.lower())
            except ValueError:
                pass
        if task_type in {"risk_analysis", "code"} or len(task.objective.split()) > 80:
            return TaskComplexity.HIGH
        if len(task.objective.split()) < 20:
            return TaskComplexity.LOW
        return TaskComplexity.MEDIUM

    @staticmethod
    def _score(
        model: RegisteredModel,
        context: RoutingContext,
        complexity: TaskComplexity,
        latency_requirement: int,
    ) -> tuple[float, tuple[str, ...]]:
        score = float(model.quality_rank * (18 if complexity is TaskComplexity.HIGH else 10))
        reasons = [f"quality rank {model.quality_rank} weighted for {complexity.value} complexity"]
        if context.scheduling.workload.value == "interactive":
            latency_points = {LatencyClass.FAST: 75, LatencyClass.BALANCED: 15, LatencyClass.THROUGHPUT: 5}[model.latency_class]
            score += latency_points
            score += max(0.0, 12.0 - model.parameter_count_billions * 4.0)
            reasons.append(f"interactive latency class contributed {latency_points} points")
        elif context.scheduling.workload.value == "background":
            efficiency = max(0.0, 50.0 - model.parameter_count_billions * 15.0)
            score += efficiency
            reasons.append(f"background size efficiency contributed {efficiency:.2f} points")
        else:
            score += model.quality_rank * 5
            reasons.append("standard workload retained balanced quality weighting")
        if model.benchmark is not None:
            score += min(20.0, model.benchmark.tokens_per_second / 10.0)
            if model.benchmark.ttft_ms <= latency_requirement:
                score += 10.0
                reasons.append("measured TTFT fits the requested latency window")
            else:
                reasons.append("measured TTFT exceeds the requested latency window")
        else:
            reasons.append("no historical benchmark is claimed")
        score -= min(20.0, context.queue_depth * 2.0)
        if context.queue_depth:
            reasons.append(f"queue depth {context.queue_depth} applied a congestion penalty")
        return score, tuple(reasons)
