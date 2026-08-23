import unittest

from runtime.config import RuntimeConfig
from runtime.errors import ConfigurationError, ValidationError
from runtime.models import Agent


class RuntimeConfigTests(unittest.TestCase):
    def test_defaults_are_valid(self) -> None:
        config = RuntimeConfig()

        self.assertEqual(config.default_model, "stage-1-stub-model")
        self.assertEqual(config.max_generated_tokens, 64)

    def test_empty_runtime_name_is_rejected(self) -> None:
        with self.assertRaises(ConfigurationError) as caught:
            RuntimeConfig(runtime_name="   ")

        self.assertEqual(caught.exception.code, "configuration_error")

    def test_non_positive_token_limit_is_rejected_with_details(self) -> None:
        with self.assertRaises(ConfigurationError) as caught:
            RuntimeConfig(max_generated_tokens=0)

        self.assertEqual(caught.exception.as_dict()["details"], {"value": 0})


class DomainValidationTests(unittest.TestCase):
    def test_agent_requires_an_objective(self) -> None:
        with self.assertRaises(ValidationError):
            Agent(agent_id="agent-1", name="Agent", objective="")


if __name__ == "__main__":
    unittest.main()
