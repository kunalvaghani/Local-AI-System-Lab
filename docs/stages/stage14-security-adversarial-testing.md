# Stage 14 — Security & Adversarial Testing

## What this stage is for

Stage 14 makes important local-runtime boundaries explicit and repeatedly tests
them with hostile inputs. It reduces the impact of prompt injection, permission
escalation, path escape, malformed data, secret leakage, runaway work, and
exfiltration attempts by keeping authority in deterministic code outside the
model. A passing suite demonstrates only the tested controls; it does not prove
that the system is secure.

## Component upgrade map

| Component | What it does in Stage 14 | Upgrade over Stage 13 |
| --- | --- | --- |
| Security configuration | Defines size/depth/node/output/process/timeout limits, path entries, global permissions, network default, and secret patterns | Makes security policy strict, versioned, and inspectable |
| Input guard | Rejects oversized, deeply nested, non-JSON, non-finite, control-character, and secret-like inputs before persistence/inference | Adds a central pre-execution boundary |
| Prompt protector | JSON-encodes the objective as explicitly untrusted data and reinforces fixed system authority | Separates user content from policy without claiming injection immunity |
| Output guard | Validates model text and structured tool data for size, shape, controls, and secret-like content | Prevents unchecked output from reaching task completion |
| Telemetry redactor | Removes detected secret strings and sensitive string fields from runtime event/metric payloads | Reduces leakage into observable evidence |
| Path policy | Requires a configured entry, rejects denied components, resolves symlinks/escapes, and permits only approved text suffixes | Narrows Stage 5 workspace-root containment |
| Security tool policy | Retains exact agent grants and imposes a global read-only `filesystem.read` ceiling with mandatory path restriction | Prevents a model or agent grant from escalating global authority |
| Network policy | Denies all current network destinations and registers no network-capable tool | Makes local-only application capability explicit |
| Subprocess policy | Requires `shell=False`, an exact executable/cwd, bounded args/command/timeout, and secret-free arguments | Documents and tests the pinned inference launch contract |
| Process limiter | Allows one concurrent inference slot around the existing backend | Adds an explicit resource ceiling above the one-worker scheduler/backend lock |
| Adversarial runner | Executes selected or all cases and emits per-case PASS/FAIL evidence | Turns security assertions into one retained machine-readable report |

## Retained adversarial matrix

| Case | Tested boundary | Result |
| --- | --- | --- |
| Prompt injection | Untrusted JSON prompt envelope; no authority/tool channel | PASS |
| Tool escalation | Missing exact agent grant | PASS |
| Path traversal | Resolved workspace escape | PASS |
| Absolute path | Relative-entry allowlist | PASS |
| Context flooding | 4,096-character objective ceiling before inference | PASS |
| Malformed structure | Depth-six JSON-like payload ceiling | PASS |
| Infinite loop | 20 ms cooperative tool deadline and cancellation signal | PASS |
| Network exfiltration | Default-deny application network policy | PASS |
| Secret input | Pattern detection before inference plus evidence redaction | PASS |
| Secret output | Model-output secret scan | PASS |
| Shell injection | Shell execution forbidden | PASS |
| Unauthorized subprocess | Exact executable allowlist | PASS |
| Process limit | Second concurrent process slot denied | PASS |
| Resource exhaustion | Tool read request above 20,000 characters rejected | PASS |

## Measurements

The retained `stage14-security-20260824T203349Z.json` reports:

- 14 cases, 14 PASS, zero FAIL, and a 100% bounded-suite pass rate;
- 2,181.687 ms total case time;
- zero real LLM calls and SQLite integrity `ok`;
- five durable runtime tasks: one completed, three `security_blocked`, and one
  `tool_failed`;
- one deterministic stub model call, three tool calls, five trace runs, and 55
  trace steps;
- 6.242 ms durable observability collection.

A separate normal-runtime verification used the real Qwen2.5 1.5B backend. It
completed with one prompt-protection event, zero injected faults, 19 trace steps,
3,370.565 ms inference, 2,760.402 ms TTFT, 105.39 tokens/s, 1,343.949 MiB peak
RAM, and 1,189 MiB VRAM delta. This is one compatibility run, not a statistically
meaningful security or performance comparison.

The final full regression suite passed 138 tests in 29.058 seconds. Ten focused Stage 14 tests cover
strict configuration, prompt encoding, input/output/secret validation, path and
tool ceilings, subprocess/process constraints, guarded runtime composition, and
the complete redacted adversarial report.

## Usage

Run the complete suite or selected cases:

```powershell
python -m runtime.security_cli
python -m runtime.security_cli --case prompt-injection --case tool-escalation
python -m benchmarks.run_stage14_security
```

Normal real-agent execution uses the guarded Stage 14 factory:

```powershell
python -m runtime.agent_cli --agent technical-explainer --database data/stage14-local.db
```

## Limits retained

- Prompt injection cannot be solved by delimiters or system prompts. The
  structural test proves separation and deterministic least privilege, not
  that every model response will follow instructions.
- Network denial is an application capability policy, not an OS firewall or
  container network namespace. The pinned local inference executable is not
  claimed to be sandboxed.
- Subprocess validation covers the configured inference launch contract; the
  current runtime exposes no general subprocess or shell tool.
- Pattern-based secret scanning has false-positive and false-negative risk.
- Validated objectives remain in the ignored local SQLite database for recovery;
  encryption-at-rest and retention automation are not implemented.
- The infinite-loop case uses a cooperative trusted handler. Python threads
  cannot safely kill hostile code, so untrusted handlers remain prohibited.
- Output validation is structural and secret-oriented, not semantic correctness,
  toxicity, factuality, or role-compliance evaluation.
- Stage 15 backend API and full runtime integration have not started.
