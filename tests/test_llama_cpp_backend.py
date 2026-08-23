import sys
import tempfile
import unittest
from pathlib import Path
from threading import Timer

from runtime.cancellation import CancellationToken
from runtime.errors import ComponentOperationError, InferenceCancelledError
from runtime.inference.config import LlamaCppConfig
from runtime.inference.llama_cpp import LlamaCppCompletionBackend
from runtime.models import InferenceRequest


FIXTURE = Path(__file__).parent / "fixtures" / "fake_llama.py"


def fake_config(model_path: Path) -> LlamaCppConfig:
    return LlamaCppConfig(
        executable_path=Path(sys.executable),
        launcher_args=(str(FIXTURE),),
        model_path=model_path,
        model_id="test/fake-gguf",
        model_revision="test-revision",
        model_sha256=None,
        executable_sha256=None,
        release="b-test",
        commit="test-commit",
        context_size=128,
        batch_size=8,
        threads=1,
        gpu_layers=0,
        flash_attention="off",
        temperature=0.0,
        seed=42,
        max_generated_tokens=16,
        prompt_format="qwen-chatml",
        system_prompt="Test system prompt.",
        resource_sample_interval_ms=0,
    )


class LlamaCppBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.model_path = Path(self.temp_dir.name) / "fake.gguf"
        self.model_path.write_bytes(b"fake model")

    def request(self) -> InferenceRequest:
        return InferenceRequest(
            task_id="task-1",
            prompt="Stream a response",
            model_id="test/fake-gguf",
            max_generated_tokens=16,
        )

    def test_streams_multiple_chunks_and_strips_ui_end_marker(self) -> None:
        backend = LlamaCppCompletionBackend(fake_config(self.model_path))
        backend.start()
        self.addCleanup(backend.shutdown)

        chunks = list(backend.stream(self.request()))
        text_chunks = [chunk.text for chunk in chunks if chunk.text]

        self.assertGreater(len(text_chunks), 1)
        self.assertEqual(
            "".join(text_chunks),
            "first streamed segment, second streamed segment, third streamed segment",
        )
        self.assertTrue(chunks[-1].is_final)
        self.assertEqual(chunks[-1].metrics.model_load_ms, 500.0)  # type: ignore[union-attr]
        self.assertEqual(chunks[-1].metrics.tokens_per_second, 200.0)  # type: ignore[union-attr]

    def test_generate_returns_real_backend_metadata_and_metrics(self) -> None:
        backend = LlamaCppCompletionBackend(fake_config(self.model_path))
        backend.start()
        self.addCleanup(backend.shutdown)

        result = backend.generate(self.request())

        self.assertEqual(result.metadata["real_llm_calls"], 1)
        self.assertEqual(result.model_id, "test/fake-gguf")
        self.assertEqual(result.metrics.prompt_tokens, 10)  # type: ignore[union-attr]

    def test_cancellation_terminates_active_subprocess(self) -> None:
        backend = LlamaCppCompletionBackend(fake_config(self.model_path))
        backend.start()
        self.addCleanup(backend.shutdown)
        token = CancellationToken()
        timer = Timer(0.08, token.cancel)
        timer.start()
        self.addCleanup(timer.cancel)

        with self.assertRaises(InferenceCancelledError):
            list(backend.stream(self.request(), token))

    def test_start_rejects_hash_mismatch(self) -> None:
        config = fake_config(self.model_path)
        config = LlamaCppConfig(
            **{
                field: getattr(config, field)
                for field in config.__dataclass_fields__
                if field != "model_sha256"
            },
            model_sha256="0" * 64,
        )
        backend = LlamaCppCompletionBackend(config)

        with self.assertRaises(ComponentOperationError) as caught:
            backend.start()

        self.assertIn("SHA-256", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
