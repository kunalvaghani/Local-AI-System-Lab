# Failed Experiments and Engineering Decisions

Failures are retained because they explain why the final design exists. They are
not edited into retroactive success.

## Experiment — Zero GPU layers as CPU isolation

### Question

Does configuring zero GPU layers eliminate GPU memory use for the CPU-safe profile?

### Hypothesis

Zero offloaded layers should produce a 0 MiB VRAM delta.

### Configuration

Pinned Qwen2.5 1.5B GGUF and llama.cpp with the initial CPU-safe profile.

### Expected

No CUDA allocation.

### Actual

llama.cpp still initialized CUDA and measured a 311 MiB VRAM allocation.

### Evidence

The exploratory and final [Stage 8 results](../../benchmarks/results/stage8-profile-comparison-20260824T122355Z.json)
retain the comparison.

### Root Cause / Interpretation

Layer offload and device initialization are separate controls.

### Decision

Add explicit `--device none`; keep the resulting 0 MiB VRAM behavior and accept
27.06 tokens/s plus higher host-memory/latency cost.

### Follow-Up Result

Repeated CPU-safe measurement reported 0 MiB VRAM delta.

## Experiment — Terminal state and result write as adjacent transactions

### Question

Can a terminal task always be assumed to have a durable output?

### Hypothesis

Short FULL-synchronous SQLite transactions would make the practical gap negligible.

### Configuration

Inject a database failure exactly at result persistence after the terminal state commit.

### Expected

Either both state and output survive or the operation rolls back visibly.

### Actual

The task remained `completed` without output. Chaos containment was 8/9, not 9/9.

### Evidence

[Stage 13 chaos result](../../benchmarks/results/stage13-chaos-20260824T193424Z.json).

### Root Cause / Interpretation

State and output cross two transactions, leaving a narrow crash window.

### Decision

Report the gap, require manual repair, and avoid automatic retry that could
duplicate model/tool side effects.

### Follow-Up Result

Stage 26 verifies normal completed evidence after API restart but correctly keeps
recovery maturity `PARTIAL`.

## Experiment — Semantic role quality from structural validation

### Question

Does a completed, non-empty two-sentence result prove an agent followed its role?

### Hypothesis

Tight system prompts and structural limits would be adequate for the MVP.

### Configuration

Two specialized agents using the same small local model with distinct prompts.

### Expected

Consistently role-correct explanations and risk summaries.

### Actual

Outputs completed and passed structural validation, but semantic drift remained possible.

### Evidence

The limitation remains in [PROJECT_STATE.md](../../PROJECT_STATE.md) and the [risk register](../risks.md).

### Root Cause / Interpretation

Shape validation is not semantic evaluation, particularly for a small nondeterministic model.

### Decision

Keep structural failure states but do not claim model accuracy or role compliance.

### Follow-Up Result

Release maturity keeps model routing/evaluation `PARTIAL`; semantic evaluation is deferred.

## Experiment — Python 3.11 Windows fault-suite cleanup

### Question

Does the verified fault suite behave identically under the machine's Python 3.11 launcher?

### Hypothesis

The standard-library-only runtime should pass unchanged.

### Configuration

Run the Stage 16 gate with Python 3.11 on Windows.

### Expected

The same 154 tests and acceptance result as Python 3.10.

### Actual

The deliberately faulted SQLite case retained a file handle through temporary-
directory cleanup and failed with `WinError 32`; Python 3.10 passed the scenario.

### Evidence

Stage 27 risk R-88 and the Stage 26 report retain the diagnostic boundary.

### Root Cause / Interpretation

The injected connection lifecycle interacts differently with Windows cleanup;
the scenario behavior itself still occurs.

### Decision

Declare Python 3.10 the verified release runtime and track 3.11 support instead
of hiding the failure or weakening the test.

### Follow-Up Result

The complete Python 3.10 Stage 26 gate passed and produced the retained release candidate.
