# Portfolio Release Guide

This is the human entry point for Local AI Systems Lab release
`0.27.0-portfolio`. The project is a verified, fully local AI runtime and
engineering workbench built for an RTX 3050 laptop GPU with 4 GB VRAM. It is a
single-user loopback release candidate, not a hosted or multi-user product.

## Recommended reading paths

### Recruiter — five minutes

1. Read the root [README](../../README.md).
2. Scan the [real product screenshots](../assets/portfolio/runtime-command-center.png).
3. Review the [measured results](benchmark-methodology-and-results.md).
4. Open the [five-minute demonstration](demo-workflow.md).

### Interviewer — thirty minutes

1. Read the [systems design](systems-design.md).
2. Read the [security and chaos model](security-and-chaos.md).
3. Inspect the [failed experiments](failed-experiments.md).
4. Use the [interview guide](interview-guide.md) to probe tradeoffs and failure behavior.
5. Trace claims into the [Stage 26 acceptance evidence](../../benchmarks/results/stage26-product-acceptance-20260827T101438Z.json).

### Engineer reproducing the project

1. Follow [setup and reproducibility](setup-and-reproducibility.md).
2. Use the [demo workflow](demo-workflow.md).
3. Read the [benchmark methodology](benchmark-methodology-and-results.md) before comparing numbers.
4. Consult the full [architecture](../architecture.md), [risk register](../risks.md), and [project state](../../PROJECT_STATE.md).

## Release contents

| Topic | Document | What it establishes |
| --- | --- | --- |
| Setup and reproducibility | [Guide](setup-and-reproducibility.md) | Exact Windows/Python/Node/model paths, stub versus real modes, and verification commands |
| Demonstration | [Workflow](demo-workflow.md) | Five-minute and extended technical demos with expected evidence |
| Benchmarks | [Methodology and results](benchmark-methodology-and-results.md) | Measurement boundaries, baselines, acceptance thresholds, results, and caveats |
| Scheduler/routing/recovery | [Systems design](systems-design.md) | Algorithms, ownership, concurrency, failure behavior, and alternatives |
| Security/reliability | [Security and chaos](security-and-chaos.md) | Deterministic authority boundaries, adversarial cases, fault injection, and limits |
| Frontend | [Design rationale](frontend-design-rationale.md) | Why the UI is an engineering instrument rather than a chat/dashboard template |
| Engineering judgment | [Failed experiments](failed-experiments.md) | What failed, evidence, interpretation, and keep/revert decisions |
| Interview preparation | [Questions and answers](interview-guide.md) | Concise, evidence-backed explanations of the principal technical decisions |

## Release decision

Stage 26 produced `release_candidate=true`; all seven product categories and all
fourteen inherited backend categories passed. Overall maturity remains
`PARTIAL` because the narrow terminal-state/output transaction gap, one-model
semantic-evaluation boundary, application-level isolation, and remote/multi-user
deployment are deliberately not relabelled as complete.
