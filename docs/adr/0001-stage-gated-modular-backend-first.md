# ADR-0001: Stage-gated, modular, backend-first delivery

- Status: Accepted
- Date: 2026-08-23
- Deciders: Project owner and engineering review

## Context

The project must demonstrate local AI systems engineering on an RTX 3050 Laptop
GPU with 4 GB VRAM, an 8-core Ryzen 7 CPU, 32 GB RAM, and no paid services. The
repository began without an implementation. A large roadmap creates a material
risk of building opaque integrations or polished UI before runtime behavior can
be measured and defended.

## Decision drivers

- Inspectable runtime logic and interview-defensible tradeoffs
- Evidence before optimization or safety/reliability claims
- Tight RAM/VRAM constraints
- A zero-cost, local-first operating model
- Failure isolation without premature distributed-system complexity
- Prevention of fabricated frontend data or contracts

## Alternatives considered

### Build the UI and backend in parallel

This could create earlier screenshots, but it encourages mocked contracts and UI
rework before scheduler, trace, and recovery semantics are known.

### Start with a black-box agent framework

This accelerates common orchestration features but hides the state, scheduling,
policy, and failure mechanics that are the portfolio's primary learning value.

### Start with C++ or microservices

Both can demonstrate systems concepts, but add build, debugging, deployment, and
failure overhead before any profile identifies a bottleneck or isolation need.

### Python-first modular monolith with stage gates

Typed in-process contracts keep component boundaries testable while preserving
fast iteration. Native components or process boundaries can be introduced later
when measurements justify them.

## Decision

Implement one approved stage at a time and stop after its evidence/report. Build
the backend completely before production frontend development. Begin runtime
implementation in Python with explicit, replaceable component interfaces and no
black-box agent framework at the core. Introduce C++ only after profiling or a
specific systems-level requirement justifies it.

## Consequences

### Positive

- Each stage produces a reviewable capability and accurate project state.
- Core runtime mechanics remain inspectable and independently testable.
- UI contracts will be based on real backend behavior.
- Optimization decisions can preserve baseline evidence.

### Negative / tradeoffs

- Visible frontend progress arrives later.
- Approval gates increase elapsed delivery time.
- Initial in-process boundaries may need revision after concurrency measurements.
- Python may eventually be insufficient for a measured hot path.

## Verification

- Every end-of-stage report must list real commands/results and stop for approval.
- `PROJECT_STATE.md` must identify only one next stage.
- Stage 1 must demonstrate a runnable lifecycle without real inference.
- Native-code proposals must include a Python baseline and before/after benchmark.
- Production frontend files must not appear before Stage 16 acceptance.

## Supersedes / superseded by

None.
