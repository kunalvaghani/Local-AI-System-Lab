# ADR-0002: Typed protocols and a standard-library synchronous skeleton

- Status: Accepted
- Date: 2026-08-23
- Deciders: Project owner and engineering review

## Context

Stage 1 must make the planned component boundaries executable without real LLM
inference or premature implementations of scheduling, persistence, routing, or
observability. The workstation has Python 3.10 and 3.11 entry points but does not
have `pytest` installed for Python 3.10.

## Decision drivers

- Replaceable and inspectable components
- A runnable lifecycle with zero network/model requirements
- Fast tests on the constrained target machine
- Minimal dependency and installation risk
- Interfaces that do not promise unimplemented later-stage behavior

## Alternatives considered

### Abstract base classes

ABCs provide nominal enforcement and shared implementation hooks. They also
couple adapters to project inheritance even when structural compatibility is
enough. They remain available if later invariants require shared base behavior.

### Dependency-injection or agent framework

A framework could automate composition but would add an external dependency and
hide the simple constructor-based dependency graph this stage should expose.

### Async-first runtime

Async interfaces could anticipate streaming and scheduling, but Stage 1 has no
concurrent workload. Choosing async semantics before Stage 2/6 evidence would
create contracts that may not match the eventual llama.cpp integration.

### Typed protocols with synchronous in-memory implementations

Python `Protocol`, frozen dataclasses, enums, and structured exceptions provide
clear boundaries with no third-party dependency. An inline scheduler and stub
backend exercise the dependency graph without claiming later capabilities.

## Decision

Use Python 3.10-compatible structural protocols for component boundaries,
constructor injection through `RuntimeComponents`, typed data models, and a
structured exception hierarchy. Keep the Stage 1 lifecycle synchronous and use
only standard-library tests and deterministic process-local components. Mark
stub output and zero real LLM calls explicitly.

## Consequences

### Positive

- The skeleton runs and tests without environment installation or network access.
- Each adapter can be replaced independently in tests and later stages.
- Protocols keep core code independent of llama.cpp, Ollama, SQLite, and web frameworks.
- The CLI demonstrates the complete current lifecycle without fake model claims.

### Negative / tradeoffs

- Runtime protocol checks verify method presence, not full semantic correctness.
- Synchronous signatures may need an evidence-driven evolution for streaming and cancellation.
- In-memory checkpoint/metric stores are neither durable nor thread-safe.
- The package currently relies on `unittest`; no coverage percentage is available.

## Verification

- All in-memory components pass runtime protocol compatibility tests.
- The integration test traverses policy, routing, scheduling, stub inference, checkpoint, and metrics boundaries.
- CLI output includes start, task creation/completion, clean shutdown, and `real_llm_calls: 0`.
- Package metadata prepares successfully with `pip --dry-run --no-build-isolation`.

## Supersedes / superseded by

None.
