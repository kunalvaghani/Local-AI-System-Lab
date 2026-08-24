# Stage 6 — Request Scheduler

## What this stage is for

Stage 6 turns inference invocation into inspectable queued work. It controls
which accepted request runs next, limits simultaneous operations, distinguishes
interactive from background work, and makes queue behavior measurable.

## Component upgrade map

| Component | Upgrade | What it does now |
| --- | --- | --- |
| Scheduler models | New typed policy/options/status/result models | Represent workload, priority, deadline, queue status, timestamps, and metrics |
| Queued scheduler | New bounded worker implementation | Accepts multiple requests, dispatches at most the configured worker count, and exposes handles |
| FIFO policy | Executable baseline | Preserves stable submission order |
| Priority policy | Executable current policy | Runs higher effective priority first with stable sequence tie-breaking |
| Workload classes | Interactive/standard/background defaults | Supply explainable priority values of 100/50/10 unless explicitly overridden |
| Aging/starvation control | Wait-time priority growth plus maximum-wait promotion | Ensures old eligible background work eventually outranks newer requests |
| Queue monitor | Independent lightweight monitor | Cancels or expires queued requests even while workers are busy |
| Timeout boundary | End-to-end deadline | Covers queue wait and operation execution, signals the active cooperative token |
| Cancellation | Handle and token control | Cancels queued work before invocation or signals running work |
| Queue metrics | Immutable aggregate/request snapshots | Reports depth, running, peak, outcomes, P50/P95/max wait, execution order, and promotions |
| Agent runtime | Scheduler options and evidence | Routes inference through the scheduler and records request metrics in results/events |
| Inference backend | Generate accepts cancellation | Allows scheduler deadlines/cancellation to reach the owned llama.cpp process |
| Process-local stores | Locks added | Keep events, checkpoints, metrics, and agent lookup coherent under concurrent callers |
| CLI | FIFO/priority comparison | Visibly proves that the same submissions execute in different controlled orders |

## Demonstrated ordering

Submission order for both policies:

```text
background -> standard -> interactive
```

FIFO execution:

```text
background -> standard -> interactive
```

Priority execution:

```text
interactive -> standard -> background
```

The scheduler never preempts work already running. Priority affects eligible
queued requests only.

## Failure and concurrency behavior

- Queued cancellation completes without invoking the operation.
- A queue deadline can expire while every worker is occupied.
- An active deadline signals cancellation and returns `task_timeout`.
- Runtime scheduler cancellation and timeout map to `CANCELLED` and `TIMEOUT`.
- Configured worker limits are verified under simultaneous controlled work.
- Shutdown stops admission and cancels queued/running logical requests.

## Boundaries and debt

- Queue state and metrics are process-local and non-durable.
- This is scheduling, not Stage 7 RAM/VRAM admission.
- Aging/default priorities are explicit baselines, not claimed optimal values.
- Timed-out non-cooperative Python operation threads cannot be forcibly killed.
- The synchronous `AgentRuntime.run()` caller waits on its queued request; an
  external asynchronous API remains Stage 15 work.

## Verification evidence

- `python -m unittest discover -s tests -v`: 57 tests passed in 1.944 seconds.
- Scheduler-focused tests passed three repeated runs before the final gate run.
- Controlled FIFO execution: `background -> standard -> interactive`.
- Controlled priority execution: `interactive -> standard -> background`.
- Priority queue-wait P50/P95: 0.1344/0.6520 ms; peak depth: 3.
- FIFO queue-wait P50/P95: 0.3727/0.7256 ms; peak depth: 3.
- Real scheduled Qwen run: 0.1786 ms queue wait, 1,988.50 ms scheduler
  execution boundary, 1,898.38 ms backend total, and 1,324.55 ms TTFT.
- Real generation: 113.77 tokens/second, 1,339.23 MiB peak child RAM,
  and 1,219 MiB observed VRAM delta.
- `python -m compileall -q runtime tests benchmarks`: exit 0.
- Package dry run resolved `local-ai-systems-lab-0.6.0` with no dependencies.
- Markdown link validation and `git diff --check`: passed.

An active-cancellation test initially exposed a race where an operation result
could be accepted immediately after its token was set. Rechecking cancellation
and deadline after outcome receipt made cancellation/timeout win deterministically;
active cancellation and shutdown regression tests now pass.

The controlled workloads are deliberately tiny. Their timings verify queue
instrumentation and policy order; they do not establish that priority has lower
latency or higher throughput for production workloads.
