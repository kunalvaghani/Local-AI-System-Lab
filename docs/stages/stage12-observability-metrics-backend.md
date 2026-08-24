# Stage 12 — Observability & Metrics Backend

## What this stage is for

Stage 12 makes the local runtime explain its recent and current behavior through
one backend report. It answers how many tasks, model calls, tool calls, routes,
failures, recoveries, and traces occurred; how long measured work took; what the
scheduler is doing now; and what CPU, RAM, GPU, and VRAM evidence is available.
It is an observability backend, not the final GUI or public task API.

## Component upgrade map

| Component | What it does in Stage 12 | Upgrade over Stage 11 |
| --- | --- | --- |
| SQLite observability source | Reads tasks, metric events, outputs, tools, recoveries, and traces in one windowed read transaction | Turns durable trace-era records into a coherent query source |
| Unified aggregator | Computes totals plus count/min/P50/P95/max/mean distributions with units | Correlates previously separate telemetry and keeps missing values explicit |
| Task telemetry model | Connects state, run, agent, model, route, scheduler, inference, hardware, failure, tool, and recovery evidence per task | Adds bounded recent-task drill-down rather than isolated records |
| Live scheduler snapshot | Reports queue depth, running work, outcomes, wait percentiles, and promotions for the current process | Exposes current queue state alongside durable historical timings |
| Live hardware snapshot | Reports source/confidence-labelled CPU, RAM, GPU, and VRAM state | Reuses Stage 7 evidence through the unified report boundary |
| Observability CLI | Runs a controlled demonstration or queries an existing SQLite database as JSON | Makes telemetry usable by people, scripts, and future API adapters |
| Stage 12 factory | Composes observability into both real and deterministic runtimes | Preserves all Stage 11 trace/replay behavior while exposing the new protocol |

## Report contract

The report is time-windowed and machine-readable. It includes:

- task states, completions, failures, model/tool calls, router decisions,
  recoveries/retries, trace runs/steps, and replay reports;
- task, queue, scheduler, tool, recovery, inference, TTFT, throughput, RAM, and
  VRAM distributions;
- current scheduler and hardware snapshots when requested;
- recent task drill-down and recent metric/lifecycle events;
- exact source labels and warnings.

Every distribution carries its sample count and unit. A missing measurement is
represented by `count: 0` and `null` statistics, never a synthetic zero. Stub
generation legitimately records a measured zero total duration, but it does not
claim TTFT, throughput, RAM, or VRAM samples.

`retries` currently equals `recovery_attempts`. This is deliberate and disclosed
in the source map because no general-purpose retry subsystem exists.

## Demonstrated behavior

The controlled runner creates four tasks:

1. one successful deterministic inference;
2. one permitted read-only tool invocation;
3. one expected default-deny tool failure;
4. one task recovered from an explicit pre-invocation checkpoint.

The report therefore expects four tasks, three completions, one failure, two
model calls, one tool call, two router decisions, one recovery/retry, and four
trace runs. It also proves the demonstration uses zero real LLM calls.

The retained `stage12-observability-20260824T163054Z.json` matched every expected
count and contained 55 trace steps. Its full live report collected in 1,504.908
ms, including a 1,498.907 ms hardware profile; a durable-only report over the
same database collected in 6.543 ms.

One real Qwen2.5 1.5B run then proved post-restart metric recovery: one completed
task/model call/route, 18 trace steps, 2,927.102 ms inference total, 2,238.325 ms
TTFT, 96.16 tokens/s, 1,343.703 MiB peak RAM, and 1,189 MiB VRAM delta.

## Operational usage

```powershell
python -m runtime.observability_cli demo
python -m runtime.observability_cli report --database data/runtime-stage12.db
python -m benchmarks.run_stage12_observability
```

Use `--window-minutes`, `--limit`, and `--event-limit` to bound the report.
Use `--no-live` for durable-only reporting without hardware or scheduler probes.
Existing-database reporting does not start a runtime or append observer lifecycle
events; a regression test compares event counts before and after the query.

## Limits retained

- The report is pull-based and process-local; there is no remote collector,
  dashboard, alerting pipeline, or public API.
- Live scheduler counters describe the runtime opened for the report. Durable
  scheduler event distributions describe historical task activity.
- CPU/GPU sampling fidelity retains the Stage 7 source and attribution caveats.
- The bounded recent-task query is intentionally simple and may need pagination
  or batched joins for much larger databases.
- SQLite trace/output payloads can contain sensitive data; redaction, retention,
  and authenticated export are still not implemented.
- Fault injection belongs to Stage 13 and has not been implemented here.
