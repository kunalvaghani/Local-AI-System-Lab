"""Two specialized agents with narrow Stage 5 tool grants."""

from __future__ import annotations

from .models import Agent, ToolCapabilityMetadata


TECHNICAL_EXPLAINER = Agent(
    agent_id="technical-explainer",
    name="Technical Explainer",
    objective=(
        "In at most 40 words, explain how keeping inference local improves "
        "privacy and how lifecycle events make the runtime inspectable."
    ),
    capabilities=frozenset({"technical-explanation", "concise-writing"}),
    system_prompt=(
        "You are a technical explainer for local AI systems. Explain that local "
        "inference keeps prompts on the device and lifecycle events record each "
        "runtime step. Never say local inference reduces privacy. Return exactly "
        "two short sentences totaling no more than 40 words."
    ),
    tool_capabilities=(
        ToolCapabilityMetadata(
            name="project_context_read",
            description="Read one approved text file inside the project root.",
            permissions=frozenset({"filesystem.read"}),
        ),
    ),
)


RISK_ANALYST = Agent(
    agent_id="risk-analyst",
    name="Runtime Risk Analyst",
    objective=(
        "During local inference on a 4 GB GPU, identify the most important risk "
        "and give one concrete mitigation in at most 40 words."
    ),
    capabilities=frozenset({"risk-analysis", "mitigation-writing"}),
    system_prompt=(
        "You are a local-inference risk analyst. Focus only on inference memory: "
        "the principal risk is GPU out-of-memory, and the concrete mitigation is "
        "a smaller quantized model or shorter context. Never discuss training or "
        "datasets. Return exactly two short sentences totaling under 40 words."
    ),
    tool_capabilities=(
        ToolCapabilityMetadata(
            name="risk_register_read",
            description="Read the fixed project risk register.",
            permissions=frozenset({"filesystem.read"}),
        ),
    ),
)


def stage3_agents() -> tuple[Agent, Agent]:
    return TECHNICAL_EXPLAINER, RISK_ANALYST
