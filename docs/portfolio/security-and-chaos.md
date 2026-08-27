# Security Model and Chaos Testing

## Security authority path

```text
Agent
  -> deterministic policy engine
  -> exact capability and permission validation
  -> bounded registered executor
  -> read-only tool
```

The model never grants authority. Tool names come from the server registry;
agent grants are exact; arguments are typed; paths must remain under configured
roots with approved suffixes; time and output are bounded. Network, shell,
process, and filesystem write permissions are globally absent. Stage 26 exposes
this same authority through a server-catalogued Safe Tool Probe without moving a
grant into browser code.

## Input, output, process, and secret controls

- Objectives and untrusted content are encoded as data, not concatenated as
  trusted instructions.
- Request size, objective length, generated tokens, context, time, task capacity,
  tool output, and experiment selection have explicit ceilings.
- The llama.cpp adapter validates executable hash/path, arguments, working
  directory, `shell=False`, timeout, cancellation, and process cleanup.
- Finite secret patterns and sensitive-key checks block representative values
  before persistence/inference; telemetry redacts sensitive attributes.
- API traces omit raw input/output payloads, system prompts, run metadata,
  absolute model paths, and detailed failures.

These are application controls, not an OS sandbox, firewall, DLP product,
penetration test, or certification. The native model process and local SQLite
database still handle sensitive local data.

## Adversarial suite

Fourteen deterministic cases cover direct prompt injection, tool escalation,
path escape, network authority, shell/process attempts, secret handling,
malformed structures, output violations, context flooding, infinite cooperative
work, and resource limits. A PASS means the expected local defense held for that
case. It does not mean the system is secure against all attacks.

The retained result is [14/14 expected defenses](../../benchmarks/results/stage14-security-20260824T203349Z.json)
with zero real model calls and database integrity `ok`.

## Chaos design

Fault adapters wrap replaceable protocol boundaries and remain inert until an
explicit bounded plan is armed. Scenarios include model/tool timeout, invalid
output, database failure, agent crash, context overflow, simulated OOM,
corrupted result, and malformed tool behavior. Every activation is task-
correlated and compares expected state/error with actual state/error.

API/UI experiments require literal confirmation, accept only server-catalogued
IDs, cap selection, and run a separate deterministic runtime with a unique
database. The serving runtime is never armed by the experiment UI.

## Reliability result

The full suite produced 9/9 expected outcomes and 1/1 successful killed-worker
recovery. Containment is intentionally 8/9 because the database result-write
fault reproduces the terminal-state/output atomicity gap. Reporting 100%
containment would hide the most useful reliability finding.

Source: [Stage 13 chaos evidence](../../benchmarks/results/stage13-chaos-20260824T193424Z.json).

## Remaining security work

- OS/container/VM isolation for untrusted native or tool code.
- Authentication, TLS, identity authorization, rate limits, and proxy trust for
  any non-loopback deployment.
- Encryption at rest, retention/deletion/export policy, and secure backups.
- Broader indirect prompt-injection and real-model semantic evaluation.
- Independent threat modelling, penetration testing, and human review.
