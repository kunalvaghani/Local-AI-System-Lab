# ADR-0006: Default-deny bounded tool runtime

- Status: Accepted
- Date: 2026-08-24

## Context

Stage 3 agents named future tools, while Stage 4 represented tool states without
granting or executing anything. Stage 5 requires a permitted agent request to be
validated and executed, and a denied request to be observable. Host filesystem,
subprocess, and network access are high-risk on a local workstation.

## Decision

Use a process-local typed registry whose definitions declare argument schemas,
required permission names, read-only/path properties, and a timeout. Authorize
with default deny: the agent must hold an exact tool-name grant containing every
required permission. Validate arguments without coercion and validate handler
results as `dict[str, Any]` envelopes.

Begin with two UTF-8 read-only tools. Resolve every caller-provided path beneath
the configured project root, reject absolute/escaping paths and non-allowlisted
suffixes, and cap returned characters. Run handlers on daemon threads with a
cooperative cancellation token and caller-visible deadline. Record execution
through the existing task state machine and structured error hierarchy.

## Consequences

- Missing grants and path violations become inspectable security blocks.
- Tool code cannot call the model or bypass task ownership through the public runtime.
- Tests can replace registry, policy, and executor independently.
- Python threads cannot forcibly terminate a non-cooperative handler. Only vetted
  cooperative handlers are allowed now; process isolation is required before
  untrusted or side-effecting tools.
- Registries and grants are process-local and static until later persistence and
  configuration stages.

## Alternatives considered

- Trust tool names declared by agents: rejected because declaration alone is not authorization.
- Allow arbitrary filesystem reads: rejected because containment is a Stage 5 requirement.
- Execute synchronously with elapsed-time checks: rejected because it cannot return at a deadline.
- Spawn a process per safe read: deferred because current handlers are vetted and tiny; process isolation remains the hardening path.
