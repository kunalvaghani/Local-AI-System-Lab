"""Deterministic subprocess fixture for llama.cpp adapter tests."""

import sys
import time


if "--version" in sys.argv:
    print("fake llama.cpp b-test")
    raise SystemExit(0)

print("0.00.100.000 I llama_completion: llama backend init", file=sys.stderr)
print(
    "0.00.200.000 I llama_completion: load the model and apply lora adapter, if any",
    file=sys.stderr,
)
time.sleep(0.03)
print("0.00.700.000 I cmn init: llama threadpool init, n_threads = 1", file=sys.stderr)
print("0.00.710.000 I generate: n_ctx = 128, n_batch = 8", file=sys.stderr)
sys.stderr.flush()

for part in (
    "first streamed segment, ",
    "second streamed segment, ",
    "third streamed segment",
):
    sys.stdout.write(part)
    sys.stdout.flush()
    time.sleep(0.06)

sys.stdout.write(" [end of text]\n\n")
sys.stdout.flush()
print("common_perf_print: load time = 10.00 ms", file=sys.stderr)
print(
    "common_perf_print: prompt eval time = 20.00 ms / 10 tokens "
    "(2.00 ms per token, 500.00 tokens per second)",
    file=sys.stderr,
)
print(
    "common_perf_print: eval time = 30.00 ms / 6 runs "
    "(5.00 ms per token, 200.00 tokens per second)",
    file=sys.stderr,
)
sys.stderr.flush()
