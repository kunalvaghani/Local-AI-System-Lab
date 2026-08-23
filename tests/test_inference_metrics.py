import unittest

from runtime.inference.metrics import parse_llama_metrics


PERF_LOG = """\
0.01.000.000 I llama_completion: load the model and apply lora adapter, if any
0.02.250.000 I cmn init: llama threadpool init, n_threads = 8
common_perf_print: load time = 49.93 ms
common_perf_print: prompt eval time = 49.71 ms / 28 tokens (1.78 ms per token, 563.31 tokens per second)
common_perf_print: eval time = 43.13 ms / 4 runs (10.78 ms per token, 92.74 tokens per second)
"""


class LlamaMetricParserTests(unittest.TestCase):
    def test_parses_model_prompt_generation_and_resource_measurements(self) -> None:
        metrics = parse_llama_metrics(
            PERF_LOG,
            startup_to_ready_ms=1600.0,
            ttft_ms=1700.0,
            total_ms=1800.0,
            peak_process_ram_mib=1300.0,
            baseline_vram_used_mib=100.0,
            peak_vram_used_mib=1400.0,
        )

        self.assertEqual(metrics.model_load_ms, 1250.0)
        self.assertEqual(metrics.prompt_tokens, 28)
        self.assertEqual(metrics.prompt_tokens_per_second, 563.31)
        self.assertEqual(metrics.generated_token_runs, 4)
        self.assertEqual(metrics.tokens_per_second, 92.74)
        self.assertEqual(metrics.internal_load_ms, 49.93)
        self.assertEqual(metrics.vram_delta_mib, 1300.0)

    def test_unobserved_values_remain_none(self) -> None:
        metrics = parse_llama_metrics(
            "no performance lines",
            startup_to_ready_ms=None,
            ttft_ms=None,
            total_ms=10.0,
            peak_process_ram_mib=None,
            baseline_vram_used_mib=None,
            peak_vram_used_mib=None,
        )

        self.assertIsNone(metrics.model_load_ms)
        self.assertIsNone(metrics.tokens_per_second)
        self.assertIsNone(metrics.vram_delta_mib)


if __name__ == "__main__":
    unittest.main()
