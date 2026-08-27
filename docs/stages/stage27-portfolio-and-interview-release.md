# Stage 27 — Portfolio & Interview Release

## Stage Completed

Stage 27 turns the accepted local AI system into an evidence-indexed portfolio
and interview release. It is for helping a recruiter reach the product story in
minutes and helping an engineer inspect architecture, tradeoffs, measurements,
failures, recovery, and security without reconstructing 26 earlier stages. It
adds no runtime authority and completes the planned 27-stage roadmap.

## What This Stage Is For

- Present the finished product through a concise README, real workbench images,
  and a five-minute reproducible demonstration.
- Explain what the scheduler, router, admission controller, persistence/recovery,
  security/chaos, and frontend components actually do.
- Connect numerical claims to retained machine-readable evidence and preserve
  methodology, hardware, one-run, and stub-versus-real-model caveats.
- Record failed experiments, known limitations, design rationale, and direct
  interview questions/answers instead of publishing only a success narrative.
- Make missing documents, broken links, invalid images, and changed evidence
  assertions fail an executable portfolio-release gate.

## Component Upgrades

| Component | What it does | Stage 27 upgrade |
| --- | --- | --- |
| Root README | Introduces and operates the project | Becomes a recruiter-first overview with architecture, five-minute demo, measured proof, documentation paths, screenshots, and limits |
| Portfolio guides | Explain the finished engineering system | Separate setup/reproducibility, demo, benchmarks, systems design, security/chaos, frontend rationale, failed experiments, and interview Q&A into direct reading paths |
| Browser capture | Produces authentic product visuals | Follows one deterministic task through five real workbench surfaces at 1440×900 and rejects a visible Runtime API error before capture |
| Release manifest | Defines the portfolio artifact contract | Declares required docs/headings, image dimensions, and exact claims against retained Stage 2/13/14/26 evidence |
| Portfolio validator | Prevents presentation/evidence drift | Strictly validates manifest fields, local Markdown links, PNG signature/IHDR, retained JSON assertions, and SHA-256 artifact inventory |
| Architecture/ADR/risk/state docs | Preserve engineering decisions and scope | Record the release-evidence layer, its alternatives, risks of stale claims/images and over-generalized numbers, and final roadmap state |

## Expected Output

- Complete recruiter/interviewer documentation for every required engineering topic.
- At least four real screenshots and one repeatable five-minute product workflow.
- Direct, caveated benchmark evidence and reproducibility instructions.
- Executable validation of documentation, links, screenshots, and retained claims.
- A finished product story whose capability and limitations are understandable
  without reading the chronological build history.

## Actual Output

- The root README and nine focused portfolio guides cover setup, demo,
  methodology/results, scheduler/routing/persistence/recovery, security/chaos,
  frontend rationale, failed experiments, known limits, and 15 interview Q&As.
- Five 1440×900 PNGs were recaptured from an owned loopback stub stack after a
  real task moved through Runtime, Scheduler, Trace/Replay, Hardware, and Security.
- `configs/portfolio-release.json` and `scripts/validate_portfolio_release.py`
  retain a machine-readable pass/fail release contract and timestamped result.
- Stage 26 remains the source for 154 backend/39 frontend acceptance, one real
  Qwen/llama.cpp inference, browser integration, failure/recovery, and bundle
  measurements; Stage 27 does not relabel deterministic captures as model quality.

## New Demonstrable Capability

A reviewer can start at the README, launch the deterministic local product with
one command, complete a five-minute Runtime → Scheduler → Trace/Replay →
Hardware → Security walkthrough, inspect five authentic screenshots, drill into
architecture and tradeoffs, verify every retained numerical claim, and use the
interview guide to discuss the design at implementation depth.

## Files Added

- `apps/web/scripts/stage27-portfolio-capture.mjs`
- `configs/portfolio-release.json`
- `scripts/validate_portfolio_release.py`
- `tests/test_portfolio_release.py`
- `docs/assets/portfolio/` (five PNG screenshots)
- `docs/portfolio/` (nine focused portfolio guides)
- `docs/adr/0027-evidence-indexed-portfolio-release.md`
- `docs/stages/stage27-portfolio-and-interview-release.md`
- `benchmarks/results/stage27-portfolio-release-*.json` (timestamped retained result)

## Files Modified

- `README.md` and `PROJECT_STATE.md`.
- Architecture, development, repository-map, risk-register, and ADR-index docs.
- Frontend package/version metadata and visible Stage identity.

## Tests Performed

- `python -m unittest discover -s tests` — 157/157 backend and release-policy tests passed.
- `npm test` — 39/39 frontend component/interaction/axe tests passed.
- `npm run build` — strict TypeScript and production Vite build passed.
- `npm run check:bundle` — compressed JavaScript remained below 256,000 bytes.
- `npm run capture:portfolio` — five real 1440×900 workbench captures completed
  from the isolated loopback stack with no visible Runtime API error.
- `python scripts/validate_portfolio_release.py` — required docs/headings, local
  links, PNGs, retained evidence assertions, and hashes passed.
- `git diff --check` — no whitespace errors.

## Measurements

- Stage 27 validator: 176/176 checks passed across 15 documents, 141 local
  links, five screenshots, and four retained evidence files; exact timing and
  hashes are retained in the timestamped result.
- Backend regression: 157 tests in 38.199 seconds.
- Frontend regression: 39 tests in 15.03 seconds.
- Production assets: 517.58 kB minified JavaScript; the release bundle gate
  measured 150,999/256,000 compressed bytes. Vite reported 60.25 kB/9.64 kB
  gzip CSS. The existing >500 kB uncompressed single-chunk warning remains.
- Screenshots: five PNGs, each 1440×900.
- Accepted Stage 26 product evidence remains 154 backend tests, 39 frontend tests,
  1,801.341 ms real-model TTFT, 103.47 tokens/s, 2.531 ms safe tool execution,
  and 150,997/256,000 gzip JavaScript bytes.

## Expected vs Actual

| Requirement | Expected | Actual | Status |
| --- | --- | --- | --- |
| Recruiter entry path | Product understood without chronological reconstruction | README provides purpose, architecture, demo, measurements, docs, and limits | PASS |
| Engineering documentation | Every requested design/operations topic covered | Nine focused guides plus architecture, ADR, risks, and stage report | PASS |
| Product screenshots | At least four authentic, useful images | Five 1440×900 workbench captures from one task-scoped flow | PASS |
| Demo workflow | Repeatable short product story | One-command setup plus a timed five-minute route workflow | PASS |
| Benchmark integrity | Method, results, hardware, and caveats are explicit | Retained Stage 2/13/14/26 JSON is linked and exact claims are validator assertions | PASS |
| Failed experiments/limits | Tradeoffs and debt are visible | Four structured failed experiments and scoped known limitations are published | PASS |
| Interview readiness | Design can be discussed at implementation depth | 15 evidence-linked questions and answers cover core architecture decisions | PASS |
| Reproducibility | A fresh reviewer can set up and verify the release | Setup guide, pinned dependencies, validation commands, and stub/real distinction are explicit | PASS |
| Release validation | Missing/drifted artifacts fail closed | Strict manifest, unit tests, link/image/evidence checks, and artifact hashes pass | PASS |
| Product maturity | Portfolio packaging does not inflate readiness | Release remains single-user loopback, overall `PARTIAL`, remote deployment `DEFERRED` | PASS |

## Problems / Technical Debt

- The release is local and single-user; the standard-library HTTP server and Vite
  preview are not an authenticated, TLS-enabled production stack.
- Real semantic evaluation still covers only one installed model/backend and is
  not a model-quality benchmark.
- The terminal-state/output transaction gap keeps persistence/recovery `PARTIAL`.
- Application least privilege is not an OS sandbox, penetration test, or security certification.
- Automated accessibility checks are not human screen-reader/zoom/forced-colors conformance.
- Screenshots are deterministic integration evidence, not real-model screenshots;
  the separate Stage 26 gate supplies real-model proof.
- The validator verifies declared artifact integrity and claims, but cannot prove
  prose quality, screenshot freshness, or cross-hardware performance generality.
- Python 3.11 Windows SQLite fault cleanup and the uncompressed frontend chunk
  warning remain tracked limitations.

## PROJECT_STATE.md Update

`PROJECT_STATE.md` now identifies Stage 27 as complete, records the recruiter-
first documentation, screenshot, and executable evidence contracts, preserves
the `PARTIAL`/`DEFERRED` boundaries, and marks the planned 27-stage roadmap complete.

## Next Stage

None — the planned 27-stage roadmap is complete. Any future implementation
requires a newly approved scope.
