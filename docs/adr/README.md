# Architecture Decision Records

ADRs preserve decisions that materially affect architecture, security,
performance, reproducibility, or stage boundaries.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-stage-gated-modular-backend-first.md) | Accepted | Stage-gated, backend-first, Python-first modular runtime |
| [0002](0002-typed-protocols-and-stdlib-skeleton.md) | Accepted | Typed protocols and a standard-library synchronous skeleton |
| [0003](0003-pinned-llama-cpp-qwen-baseline.md) | Accepted | Pinned llama.cpp subprocess and Qwen GGUF baseline |

## Process

1. Copy `template.md` and assign the next four-digit number.
2. Record context and evidence available at decision time.
3. Compare real alternatives, including the cost of doing nothing.
4. Mark the status `Proposed`, `Accepted`, `Superseded`, or `Rejected`.
5. Do not rewrite accepted history; add a superseding ADR when a decision changes.
6. Link measurements, tests, failed experiments, and successor ADRs when available.
