"""Typed runtime configuration with fail-fast validation."""

from dataclasses import dataclass

from .errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Core runtime configuration independent of a specific backend."""

    runtime_name: str = "local-ai-systems-lab"
    default_model: str = "stage-1-stub-model"
    max_generated_tokens: int = 64
    stub_response_prefix: str = "STUB (no LLM inference):"

    def __post_init__(self) -> None:
        if not self.runtime_name.strip():
            raise ConfigurationError("runtime_name must not be empty")
        if not self.default_model.strip():
            raise ConfigurationError("default_model must not be empty")
        if self.max_generated_tokens <= 0:
            raise ConfigurationError(
                "max_generated_tokens must be greater than zero",
                details={"value": self.max_generated_tokens},
            )
        if not self.stub_response_prefix.strip():
            raise ConfigurationError("stub_response_prefix must not be empty")
