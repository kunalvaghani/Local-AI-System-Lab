# ADR-0027 — Evidence-indexed portfolio release

- Status: Accepted
- Date: 2026-08-27
- Stage: 27

## Context

The product already had implementation reports, retained benchmark JSON, and a
complete acceptance gate, but the evidence was organized for stage-by-stage
development rather than a recruiter or interviewer. A portfolio release needs a
short entry path, real product images, a repeatable five-minute demonstration,
and direct links from claims to machine-readable evidence. Documentation can
also silently drift after code or evidence changes.

## Decision

Publish a recruiter-first root README and a focused `docs/portfolio` collection.
Separate setup/reproducibility, demo, measured results, systems design,
security/chaos, frontend rationale, failed experiments, and interview material
so each audience can follow the shortest useful path.

Treat screenshots and claims as release artifacts rather than decoration. A
versioned manifest declares required documents, headings, PNG dimensions, and
exact assertions against retained Stage 2, 13, 14, and 26 JSON evidence. A
standard-library validator checks the manifest, every local Markdown link, PNG
headers/dimensions, evidence values, and artifact hashes. Browser capture runs
against a locally owned stack and rejects a visible runtime error before saving
the release images.

Keep the release honest: deterministic stub screenshots demonstrate product
integration; the separate retained Stage 26 gate proves one real local-model
call. Neither screenshots, automated accessibility checks, nor bounded security
scenarios are presented as semantic evaluation, certification, or deployment
hardening.

## Consequences

- A reviewer can understand the project, reproduce it, and reach primary
  evidence without reading 27 chronological reports.
- Documentation regressions, missing images, broken links, and changed retained
  claims become executable release failures.
- Screenshots remain reproducible and are tied to the same local API contract as
  the product instead of being hand-edited mockups.
- Hardware-specific numbers, local-only serving, partial recovery, accessibility
  scope, and security scope remain prominent limitations.
- The validator checks integrity and declared claims; it does not prove prose is
  complete, screenshots are recent, or measurements generalize to other hosts.

## Alternatives considered

| Alternative | Decision | Reason |
| --- | --- | --- |
| Link only the chronological stage reports | Rejected | It makes the reviewer reconstruct the product story and key tradeoffs |
| Use mockups or manually edited screenshots | Rejected | They do not demonstrate the running application or visible failure boundaries |
| Copy benchmark numbers into prose without source assertions | Rejected | Claims can drift from retained evidence without a failing gate |
| Re-run the real model for every screenshot | Rejected | It makes visual capture slow and nondeterministic; real inference is already a separate mandatory acceptance sub-gate |
| Present 14/14 adversarial cases as certification | Rejected | The suite proves only bounded deterministic defenses in a local lab scope |
| Add a documentation framework | Rejected | Markdown and a small standard-library validator meet the release need without another runtime or bundle dependency |

## Evidence

- `configs/portfolio-release.json`
- `scripts/validate_portfolio_release.py`
- `tests/test_portfolio_release.py`
- `apps/web/scripts/stage27-portfolio-capture.mjs`
- `docs/portfolio/README.md`
- `docs/assets/portfolio/`
- `benchmarks/results/stage26-product-acceptance-20260827T101438Z.json`
