# Stage 5 — Tool Runtime & Permission Foundations

## What this stage is for

Stage 5 converts agent tool names from inert metadata into a narrow execution
boundary. An agent can request a registered safe tool, but execution occurs only
after identity, exact grant, permission-set, argument, path, timeout, and result
checks. This is the minimum trustworthy foundation for later agent/tool loops.

## Component upgrade map

| Component | Upgrade | What it does now |
| --- | --- | --- |
| Tool models | Typed definitions, requests, permissions, results | Makes arguments, grants, timeouts, outputs, and task identity inspectable data |
| Tool registry | New process-local registry | Resolves exact names and rejects duplicate or missing tools structurally |
| Argument validator | New strict validator | Rejects missing, unknown, and incorrectly typed arguments without coercion; supplies declared defaults |
| Tool policy | New default-deny policy | Requires an exact agent grant containing all tool permissions |
| Tool executor | New bounded daemon-thread executor | Executes vetted handlers, observes external cancellation, enforces a caller-visible deadline, wraps failures, validates result shape |
| Safe tools | Two read-only readers | Reads project context or the fixed risk register as UTF-8 with suffix, size, and resolved-root restrictions |
| Agent definitions | Grants replace future metadata | Technical Explainer may read project context; Risk Analyst may read only the risk register |
| Agent runtime | New `run_tool()` path | Owns tool tasks, emits lifecycle evidence, validates result identity, and maps failures to terminal states |
| State machine | Tool-only success edge | Permits `waiting_for_tool -> validating -> completed` and planning-time tool lookup failure |
| Error hierarchy | Tool-specific structured errors | Distinguishes missing tools, duplicate registration, bad arguments, denial, path block, timeout, cancellation, handler failure, and invalid result |
| CLI | New `runtime.tool_cli` | Demonstrates one allowed request and one expected denied request without loading an LLM |

## Demonstrated flows

Permitted:

```text
technical-explainer
  -> project_context_read(README.md)
  -> grant + filesystem.read accepted
  -> contained read
  -> structured ToolResult
  -> completed
```

Denied:

```text
risk-analyst
  -> project_context_read(README.md)
  -> no exact tool grant
  -> tool_permission_denied
  -> security_blocked
```

The denied handler is never invoked. Path escapes such as `../outside.md` are
also denied and end in `security_blocked`.

## Boundaries and debt

- Only vetted, read-only local tools exist; there are no write, subprocess, or network tools.
- Cancellation is cooperative inside handlers. A non-cooperative daemon thread
  may outlive the caller-visible timeout; untrusted tools require process isolation.
- No queue, priority, starvation policy, or central task cancellation API exists.
  Those belong to Stage 6.
- Registry, grants, events, and histories are process-local and non-durable.
- This is containment and default-deny application policy, not an OS sandbox.

## Verification evidence

- `python -m unittest discover -s tests -v`: 42 tests passed in 1.699 seconds.
- `python -m runtime.tool_cli --demo`: exit 0 with both expected branches.
- Permitted tool boundary: 2.9874 ms, five-state completed history, zero model calls.
- Denied request: `tool_permission_denied`, three-state `security_blocked` history.
- `python -m compileall -q runtime tests benchmarks`: exit 0.
- Package dry run: `local-ai-systems-lab-0.5.0` resolves with no dependencies.
- `git diff --check`: exit 0; line-ending notices only.
