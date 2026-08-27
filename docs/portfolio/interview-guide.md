# Interview Questions and Evidence-Backed Answers

## 1. Why build a custom runtime instead of LangChain or LangGraph?

The project is intended to demonstrate state, scheduling, admission, routing,
tool authority, persistence, and failure mechanics. Framework ownership would
hide those boundaries. Commodity UI/query behavior still uses libraries where
the abstraction is not the portfolio subject.

## 2. Why use a modular monolith?

One workstation and one GPU do not require distributed deployment. In-process
protocols keep causality inspectable and tests replaceable. Service extraction is
deferred until independent scaling or isolation is measured.

## 3. How does scheduling work?

A bounded worker queue supports FIFO and stable priority, wait-time aging,
oldest-request promotion, queue monitoring, end-to-end deadlines, cooperative
cancellation, and measured queue/outcome statistics. One real worker matches the
measured single-model GPU capacity.

## 4. How do you avoid GPU OOM?

The runtime profiles current hardware, estimates host/VRAM needs with explicit
reserves, chooses a model/profile, re-admits the exact configuration, and can
reduce context/offload, fall back, queue, or reject. Estimates are compared with
measurements and are not presented as guarantees.

## 5. How is model routing explainable?

Candidates are filtered by actual artifact/backend availability, scored using
workload/capability/latency/resource policy, and returned with reasons and
rejections. Compute budgets cap calls, tokens, time, and estimated memory.

## 6. What is deterministic replay here?

Hash-chain integrity and deterministic state reducers are replayed. Model
generation is observed, not regenerated; tool side effects are skipped. Outcomes
explicitly say matched, diverged, observed, skipped, or integrity failure.

## 7. What survives a crash?

SQLite persists task/state/checkpoint/output/tool/trace/metric evidence. A killed
worker can resume only from a committed pre-invocation recovery checkpoint.
Arbitrary model/tool side effects are not automatically retried.

## 8. What is the most important known reliability gap?

Terminal state and output are adjacent transactions. An injected result-write
failure can leave `completed` without output. The project reports 8/9 containment
and prefers visible repair over unsafe duplication.

## 9. What makes tool execution safe?

Authority is deterministic: exact registered tool, exact agent grant, global
permission ceiling, typed arguments, allowed roots/suffixes, bounded time/output,
and no shell/network/process/write tools. Model text cannot grant capability.

## 10. Is the system secure?

No certification claim is made. Fourteen bounded adversarial cases pass, but the
controls are application-level. OS isolation, authentication, TLS, remote
authorization, DLP completeness, and independent penetration testing are absent.

## 11. Why SQLite?

It provides inspectable transactions, WAL, migration, integrity checks, and
simple local durability without operating another service. It is appropriate for
one host, not distributed coordination or multi-process active ownership.

## 12. How do you distinguish missing data from zero?

Backend reports preserve null/sample count/source/confidence. The UI renders
Unavailable and omits semantic meters when measurements are absent. A zero is
shown only when the source actually reports zero.

## 13. How was performance optimized?

The project retained a five-run cold baseline, measured four resource profiles,
found that zero GPU layers still allocated VRAM, changed to explicit device
isolation, and kept the measured tradeoff. Release thresholds are tracked before
the acceptance run.

## 14. Why does the frontend avoid heavy visualization libraries?

Semantic tables, meters, ordered timelines, and bounded CSS bars satisfy the
current data and accessibility requirements. The gzip gate passes at 150,997
bytes. Graph/WebGL/chart/virtualization dependencies remain evidence-triggered.

## 15. What does release candidate mean?

All required backend/product checks pass for one measured single-user loopback
machine. Overall maturity remains `PARTIAL`; it does not mean production,
multi-user, hosted, semantically accurate, certified secure, or universally fast.

## Evidence to open during an interview

- [Architecture](../architecture.md)
- [Product acceptance JSON](../../benchmarks/results/stage26-product-acceptance-20260827T101438Z.json)
- [Benchmark methodology](benchmark-methodology-and-results.md)
- [Failed experiments](failed-experiments.md)
- [Risk register](../risks.md)
- [ADR index](../adr/README.md)
