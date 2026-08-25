# ADR-0015 — Deterministic Security Boundaries and Adversarial Evidence

- Status: Accepted
- Date: 2026-08-25

## Context

Stage 13 could activate operational faults but did not centrally constrain task
shape, secret-like content, prompt authority, global tool permissions, network
capabilities, or subprocess policy. Several earlier controls were strong but
distributed: exact tool grants, resolved-root filesystem reads, typed arguments,
cooperative deadlines, one inference worker, hash-pinned artifacts, and
`shell=False` argument arrays.

Prompt instructions alone are not a security boundary. OWASP recommends
separating untrusted content, applying least privilege, validating input/output,
and enforcing critical authorization outside the model. It also states that
prompt injection has no foolproof prevention. See the official
[OWASP prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[system-prompt leakage guidance](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/),
and [improper-output handling guidance](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/).

## Decision

Add a strict, file-backed Stage 14 policy and enforce it through deterministic
code outside the model:

- validate objective length and JSON-like payload depth, nodes, strings,
  control characters, finite numbers, and secret-like content before persistence;
- encode the objective as an explicitly untrusted JSON string and retain fixed
  system authority;
- validate model and tool outputs before completion;
- redact secret-like strings and sensitive string fields from lifecycle/metric data;
- replace broad root containment with configured entry, component, and suffix
  allowlists for current read-only tools;
- retain exact agent grants and add a global read-only permission ceiling;
- deny network capability by default and register no network, shell, process,
  write, or escalation tool;
- validate subprocess executable identity, argument count/length, working
  directory, timeout, secret-free arguments, and `shell=False`;
- wrap inference in a one-slot process limiter while retaining scheduler timeout
  and native cancellation/termination;
- produce a local, deterministic PASS/FAIL adversarial report with redacted evidence.

The tests demonstrate these named controls. They do not certify the application,
prove model alignment, or establish an OS sandbox.

## Alternatives considered

- Keyword-block every injection phrase: rejected because wording is unbounded,
  false positives are high, and model behavior cannot become an authorization
  boundary.
- Give the model security decisions in its system prompt: rejected because tool,
  path, network, secret, and subprocess authorization must remain deterministic.
- Add a general shell or network tool and attempt to sandbox it in Python:
  rejected; no current product requirement justifies that attack surface.
- Claim success after unit tests: rejected. The retained suite records exact
  scenarios, results, limitations, durable states, and database integrity.
- Introduce containers/VM isolation now: deferred because current tools are
  fixed read-only handlers. Isolation is required before admitting untrusted or
  side-effecting code.

## Consequences

- Ordinary Stage 14 tasks receive bounded input/output validation and an
  untrusted-objective prompt envelope.
- Lifecycle telemetry no longer stores raw objectives in `task.created`; it
  stores hash and character count. Durable tasks still retain validated local
  objectives for recovery, so database access and retention remain sensitive.
- Network is denied at the application capability layer, not at the operating
  system firewall layer.
- Secret detection is pattern-based and can have false positives or negatives.
- Cooperative Python handlers still cannot be forcibly killed; the registry
  continues to prohibit untrusted handlers.
- The retained Stage 14 result passes 14/14 bounded cases with zero real LLM calls
  and SQLite integrity `ok`.

## Evidence

- `configs/security.json`
- `tests/test_security.py`
- `benchmarks/results/stage14-security-20260824T203349Z.json`
- `docs/stages/stage14-security-adversarial-testing.md`
