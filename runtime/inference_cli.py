"""CLI for real streamed local inference through the llama.cpp backend."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from threading import Timer
from uuid import uuid4

from .cancellation import CancellationToken
from .errors import InferenceCancelledError, LabError, ValidationError
from .inference import LlamaCppCompletionBackend, load_llama_cpp_config
from .models import InferenceRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stream a real local GGUF response through our inference backend.",
    )
    parser.add_argument(
        "--config",
        default="configs/inference-baseline.json",
        help="Path to the pinned Stage 2 configuration.",
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Buffer output and emit one JSON document instead of live text.",
    )
    parser.add_argument(
        "--cancel-after-ms",
        type=int,
        default=None,
        help="Request cancellation after this delay; useful for verification.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    token = CancellationToken()
    backend = None
    cancellation_timer = None
    try:
        config = load_llama_cpp_config(Path(args.config))
        backend = LlamaCppCompletionBackend(config)
        backend.start()
        request = InferenceRequest(
            task_id=str(uuid4()),
            prompt=args.prompt,
            system_prompt=args.system_prompt,
            model_id=config.model_id,
            max_generated_tokens=args.max_tokens or config.max_generated_tokens,
        )
        if args.cancel_after_ms is not None:
            if args.cancel_after_ms <= 0:
                raise ValidationError("--cancel-after-ms must be greater than zero")
            cancellation_timer = Timer(args.cancel_after_ms / 1_000.0, token.cancel)
            cancellation_timer.start()

        parts: list[str] = []
        metrics = None
        chunk_count = 0
        for chunk in backend.stream(request, token):
            if chunk.text:
                chunk_count += 1
                parts.append(chunk.text)
                if not args.json:
                    print(chunk.text, end="", flush=True)
            if chunk.is_final:
                metrics = chunk.metrics

        output = "".join(parts)
        payload = {
            "backend": backend.name,
            "backend_version": backend.version,
            "model": config.model_id,
            "model_revision": config.model_revision,
            "output": output,
            "stream_chunks": chunk_count,
            "metrics": metrics.as_dict() if metrics is not None else None,
        }
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print()
            print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 0
    except KeyboardInterrupt:
        token.cancel()
        print("Inference cancellation requested.", file=sys.stderr)
        return 130
    except InferenceCancelledError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 130
    except LabError as error:
        print(json.dumps(error.as_dict(), sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if cancellation_timer is not None:
            cancellation_timer.cancel()
        if backend is not None:
            backend.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
