import type { CSSProperties } from "react";

import type { Distribution, InferenceMetrics, MetricsData, RecentTaskTelemetry } from "../../api/types";
import { useSelectedTaskId } from "../../hooks/useSelectedTaskId";
import { useHardwareQuery, useMetricsQuery, useModelsQuery, useSchedulerQuery, useTaskQuery } from "../../query/runtimeQueries";
import { StatusToken, type StatusTone } from "../StatusToken";

type PerformanceLabProps = { focus: "hardware" | "metrics" };
type Signal = { label: string; value: string; source: string; tone: StatusTone };

const terminalStatuses = new Set(["completed", "failed", "cancelled", "timed_out"]);
const distributionRows = [
  ["ttft_ms", "First token"], ["generation_tokens_per_second", "Generation throughput"],
  ["queue_wait_ms", "Queue delay"], ["scheduler_execution_ms", "Scheduler execution"],
  ["inference_total_ms", "Inference total"], ["task_duration_ms", "Task duration"],
  ["peak_process_ram_mib", "Peak process RAM"], ["vram_delta_mib", "VRAM delta"],
] as const;

function formatNumber(value: number | null | undefined, digits = 1) {
  return value == null ? "Unavailable" : new Intl.NumberFormat(undefined, { maximumFractionDigits: digits }).format(value);
}

function metric(value: number | null | undefined, unit: string, digits = 1) {
  return value == null ? "Unavailable" : `${formatNumber(value, digits)} ${unit}`;
}

function percent(used: number | null | undefined, total: number | null | undefined) {
  if (used == null || total == null || total <= 0) return null;
  return Math.min(100, Math.max(0, used / total * 100));
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function profileFrom(metadata: Record<string, unknown> | undefined) {
  if (!metadata) return null;
  if (isObject(metadata.inference_profile)) return metadata.inference_profile;
  const selection = isObject(metadata.profile_selection) ? metadata.profile_selection : null;
  return selection && isObject(selection.selected_profile) ? selection.selected_profile : null;
}

function profileValue(profile: Record<string, unknown> | null, key: string) {
  const value = profile?.[key];
  return typeof value === "string" || typeof value === "number" ? String(value) : "Unavailable";
}

function distribution(data: MetricsData | undefined, key: string) {
  return data?.distributions[key];
}

function p50Signal(label: string, selected: number | null | undefined, unit: string, sample: Distribution | undefined, retained: number | null | undefined): Signal {
  if (selected != null) return { label, value: metric(selected, unit), source: "Selected task · measured", tone: "healthy" };
  if (sample && sample.count > 0 && sample.p50 != null) return { label, value: metric(sample.p50, sample.unit), source: `60m P50 · ${sample.count} sample${sample.count === 1 ? "" : "s"}`, tone: "healthy" };
  if (retained != null) return { label, value: metric(retained, unit), source: "Retained model benchmark · not live", tone: "partial" };
  return { label, value: "Unavailable", source: "No measured sample", tone: "unavailable" };
}

function CapacityMeter({ label, value, detail }: { label: string; value: number | null; detail: string }) {
  return <div className="capacity-meter"><div><span>{label}</span><strong>{value === null ? "Unavailable" : `${formatNumber(value)}%`}</strong></div>{value === null ? <span className="capacity-meter-unavailable" aria-label={`${label} unavailable`}>No measurement</span> : <meter aria-label={label} min="0" max="100" value={value} />}<small>{detail}</small></div>;
}

function SignalCard({ signal }: { signal: Signal }) {
  const label = signal.tone === "partial" ? "Retained" : signal.tone === "healthy" ? "Measured" : "No sample";
  return <article className="performance-signal"><div><span>{signal.label}</span><StatusToken tone={signal.tone}>{label}</StatusToken></div><strong>{signal.value}</strong><small>{signal.source}</small></article>;
}

function DistributionRow({ label, sample }: { label: string; sample: Distribution | undefined }) {
  return <tr><th scope="row">{label}<small>{sample?.unit ?? "No unit"}</small></th><td>{sample?.count ?? 0}</td><td>{metric(sample?.p50, sample?.unit ?? "")}</td><td>{metric(sample?.p95, sample?.unit ?? "")}</td><td>{metric(sample?.max, sample?.unit ?? "")}</td></tr>;
}

function RecentTaskRow({ task, maximum }: { task: RecentTaskTelemetry; maximum: number }) {
  const width = maximum > 0 ? Math.max(2, task.duration_ms / maximum * 100) : 2;
  return <li className="history-row"><div className="history-identity"><StatusToken tone={task.state === "completed" ? "healthy" : task.failure ? "critical" : "unknown"}>{task.state ?? "unknown"}</StatusToken><code>{task.task_id}</code><time dateTime={task.created_at_utc}>{new Date(task.created_at_utc).toLocaleTimeString()}</time></div><div className="history-duration"><i style={{ "--history-width": `${width}%` } as CSSProperties} /><strong>{metric(task.duration_ms, "ms")}</strong></div><div className="history-facts"><span>{task.model_id ?? "No model"}</span><span>TTFT {metric(task.inference_metrics?.ttft_ms, "ms")}</span><span>{metric(task.inference_metrics?.tokens_per_second, "tok/s")}</span><span>Queue {metric(task.scheduler.queue_wait_ms, "ms")}</span></div></li>;
}

function PerformanceLab({ focus }: PerformanceLabProps) {
  const { taskId } = useSelectedTaskId();
  const hardware = useHardwareQuery();
  const metrics = useMetricsQuery();
  const models = useModelsQuery();
  const scheduler = useSchedulerQuery();
  const task = useTaskQuery(taskId);
  const data = hardware.data;
  const ramUsed = percent(data?.ram.used_mib, data?.ram.total_mib);
  const vramUsed = percent(data?.gpu?.used_vram_mib, data?.gpu?.total_vram_mib);
  const selectedInference: InferenceMetrics | undefined | null = task.data?.result?.inference_metrics;
  const selectedModelId = task.data?.result?.model_id;
  const selectedModel = selectedModelId ? models.data?.models.find((model) => model.model_id === selectedModelId) : models.data?.models.find((model) => model.available);
  const selectedRecent = metrics.data?.recent_tasks.find((item) => item.task_id === taskId);
  const selectedRequest = scheduler.data?.requests.find((item) => item.task_id === taskId);
  const profile = profileFrom(task.data?.result?.metadata);
  const workload = typeof task.data?.input_data.workload === "string" ? task.data.input_data.workload : null;
  const budget = workload ? models.data?.compute_budgets[workload] : undefined;
  const ttft = p50Signal("Time to first token", selectedInference?.ttft_ms, "ms", distribution(metrics.data, "ttft_ms"), selectedModel?.benchmark?.ttft_ms);
  const throughput = p50Signal("Generation throughput", selectedInference?.tokens_per_second, "tok/s", distribution(metrics.data, "generation_tokens_per_second"), selectedModel?.benchmark?.tokens_per_second);
  const queue = p50Signal("Queue delay", selectedRequest?.queue_wait_ms ?? selectedRecent?.scheduler.queue_wait_ms, "ms", distribution(metrics.data, "queue_wait_ms"), null);
  const schedulerThroughput: Signal = scheduler.data ? { label: "Scheduler throughput", value: `${scheduler.data.completed} / ${scheduler.data.submitted}`, source: "Completed / submitted · current process", tone: "healthy" } : { label: "Scheduler throughput", value: "Unavailable", source: "No scheduler snapshot", tone: "unavailable" };
  const recentTasks = metrics.data?.recent_tasks ?? [];
  const maximumDuration = Math.max(1, ...recentTasks.map((item) => item.duration_ms));
  const active = task.data ? !terminalStatuses.has(task.data.status) : scheduler.data ? scheduler.data.running > 0 : false;
  const warnings = [...new Set([...(hardware.data?.warnings ?? []), ...(metrics.data?.warnings ?? [])])];

  return <section className="performance-lab" data-focus={focus} aria-labelledby="performance-lab-title">
    <div className="performance-heading"><div><p className="eyebrow">Measured local capacity · 60 minute evidence window</p><h2 id="performance-lab-title">Hardware &amp; performance lab</h2><p>Investigate resource pressure, inference latency, throughput, model choice, and exact reported configuration while workloads execute.</p></div><StatusToken tone={active ? "active" : hardware.isError || metrics.isError ? "critical" : hardware.isPending || metrics.isPending ? "queued" : "healthy"}>{active ? "Workload active" : hardware.isError || metrics.isError ? "Evidence partial" : hardware.isPending || metrics.isPending ? "Collecting" : "Measured"}</StatusToken></div>

    {hardware.isError || metrics.isError || models.isError || scheduler.isError ? <div className="runtime-error" role="alert"><strong>Some performance evidence is unavailable.</strong><ul>{[hardware.error, metrics.error, models.error, scheduler.error].filter(Boolean).map((error) => <li key={error!.message}>{error!.message}</li>)}</ul></div> : null}

    <div className="capacity-board" aria-label="Current hardware capacity">
      <article className="capacity-card"><div className="capacity-card-title"><span>CPU</span><StatusToken tone={data ? "healthy" : "unavailable"}>{data?.cpu.confidence ?? "No sample"}</StatusToken></div><strong>{data?.cpu.model ?? "Unavailable"}</strong><dl><div><dt>Logical processors</dt><dd>{formatNumber(data?.cpu.logical_processors, 0)}</dd></div><div><dt>Physical cores</dt><dd>{formatNumber(data?.cpu.physical_cores, 0)}</dd></div></dl><small>{data?.cpu.source ?? "GET /v1/hardware"}</small></article>
      <article className="capacity-card"><div className="capacity-card-title"><span>RAM</span><StatusToken tone={ramUsed === null ? "unavailable" : ramUsed > 85 ? "warning" : "healthy"}>{data?.ram.confidence ?? "No sample"}</StatusToken></div><CapacityMeter label="RAM used" value={ramUsed} detail={`${formatNumber(data?.ram.used_mib)} / ${formatNumber(data?.ram.total_mib)} MiB`} /><small>{data?.ram.source ?? "GET /v1/hardware"}</small></article>
      <article className="capacity-card"><div className="capacity-card-title"><span>GPU</span><StatusToken tone={data?.gpu ? "healthy" : "unavailable"}>{data?.gpu?.confidence ?? "No sample"}</StatusToken></div><strong>{data?.gpu?.name ?? "Unavailable"}</strong><CapacityMeter label="GPU utilization" value={data?.gpu?.utilization_percent ?? null} detail={data?.gpu?.temperature_c == null ? "Temperature unavailable" : `${formatNumber(data.gpu.temperature_c)} °C`} /><small>{data?.gpu?.source ?? "GET /v1/hardware"}</small></article>
      <article className="capacity-card"><div className="capacity-card-title"><span>VRAM</span><StatusToken tone={vramUsed === null ? "unavailable" : vramUsed > 85 ? "warning" : "healthy"}>{vramUsed === null ? "No sample" : "Measured"}</StatusToken></div><CapacityMeter label="VRAM used" value={vramUsed} detail={`${formatNumber(data?.gpu?.used_vram_mib)} / ${formatNumber(data?.gpu?.total_vram_mib)} MiB`} /><small>{data?.gpu?.free_vram_mib == null ? "Free VRAM unavailable" : `${formatNumber(data.gpu.free_vram_mib)} MiB free`}</small></article>
    </div>
    <p className="performance-provenance">Captured {data?.captured_at_utc ?? "not yet"} · profiler {data ? `${formatNumber(data.profile_ms, 3)} ms` : "unavailable"}. CPU percentage is not exposed by the profiler; topology is shown instead. Missing measurements remain unavailable, never zero-filled.</p>

    <div className="performance-signal-grid" aria-label="Inference and scheduler signals">{[ttft, throughput, queue, schedulerThroughput].map((signal) => <SignalCard key={signal.label} signal={signal} />)}</div>

    <div className="performance-analysis-grid">
      <article className="distribution-panel"><div className="panel-title-row"><div><p className="eyebrow">Observed distributions</p><h3>Latency &amp; resource envelope</h3></div><StatusToken tone={metrics.data ? "healthy" : "unavailable"}>{metrics.data ? `${metrics.data.totals.tasks} tasks` : "No report"}</StatusToken></div><div className="table-scroll"><table><thead><tr><th scope="col">Metric</th><th scope="col">N</th><th scope="col">P50</th><th scope="col">P95</th><th scope="col">Max</th></tr></thead><tbody>{distributionRows.map(([key, label]) => <DistributionRow key={key} label={label} sample={distribution(metrics.data, key)} />)}</tbody></table></div><p className="performance-provenance">Generated {metrics.data?.generated_at_utc ?? "not yet"} · collection {metric(metrics.data?.collection_ms, "ms", 3)}. Empty distributions stay unavailable.</p></article>

      <article className="configuration-panel"><div className="panel-title-row"><div><p className="eyebrow">Selected execution</p><h3>Model &amp; configuration</h3></div><StatusToken tone={task.data ? "healthy" : taskId ? "unavailable" : "partial"}>{task.data?.status ?? (taskId ? "Not found" : "Registry baseline")}</StatusToken></div>{taskId ? <p className="configuration-task-id">Task <code>{taskId}</code></p> : null}<dl className="configuration-grid"><div><dt>Model</dt><dd>{selectedModel?.display_name ?? selectedModelId ?? "Unavailable"}</dd></div><div><dt>Model ID</dt><dd>{selectedModelId ?? selectedModel?.model_id ?? "Unavailable"}</dd></div><div><dt>Profile</dt><dd>{profileValue(profile, "profile_id")}</dd></div><div><dt>Context</dt><dd>{profileValue(profile, "context_size")}</dd></div><div><dt>Batch / ubatch</dt><dd>{profile ? `${profileValue(profile, "batch_size")} / ${profileValue(profile, "ubatch_size")}` : "Unavailable"}</dd></div><div><dt>Threads</dt><dd>{profileValue(profile, "threads")}</dd></div><div><dt>GPU layers</dt><dd>{profileValue(profile, "gpu_layers")}</dd></div><div><dt>Device</dt><dd>{profileValue(profile, "devices")}</dd></div></dl>{budget ? <div className="budget-strip"><span>{workload} budget</span><strong>{budget.max_generated_tokens} tokens · {budget.total_time_ms.toLocaleString()} ms · {budget.max_ram_mib.toLocaleString()} MiB RAM · {budget.max_vram_mib.toLocaleString()} MiB VRAM</strong></div> : <p className="panel-empty">Select a task with reported workload/profile metadata to inspect its exact applied configuration. Registry benchmarks do not imply a live selection.</p>}</article>
    </div>

    <article className="history-panel"><div className="panel-title-row"><div><p className="eyebrow">Bounded durable history</p><h3>Recent workload trend</h3></div><span>{recentTasks.length} reported</span></div>{recentTasks.length ? <ol className="history-list">{recentTasks.map((item) => <RecentTaskRow key={item.task_id} maximum={maximumDuration} task={item} />)}</ol> : <p className="panel-empty">No tasks fall inside the current 60-minute report. A continuous time series is not inferred.</p>}<p className="performance-provenance">Bars compare total task duration across the bounded recent-task response. They are not a background hardware sampler.</p></article>

    <article className="model-candidates-panel"><div className="panel-title-row"><div><p className="eyebrow">Availability-gated registry</p><h3>Model candidates</h3></div><span>{models.data?.models.length ?? 0} registered</span></div><ul>{models.data?.models.map((model) => <li key={model.model_id}><StatusToken tone={model.available ? "healthy" : "unavailable"}>{model.available ? "Available" : "Unavailable"}</StatusToken><div><strong>{model.display_name}</strong><small>{model.quantization} · {model.parameter_count_billions}B · {model.latency_class}</small></div><dl><div><dt>Retained TTFT</dt><dd>{metric(model.benchmark?.ttft_ms, "ms")}</dd></div><div><dt>Retained throughput</dt><dd>{metric(model.benchmark?.tokens_per_second, "tok/s")}</dd></div><div><dt>Profile</dt><dd>{model.benchmark?.profile_id ?? "Unavailable"}</dd></div></dl></li>) ?? <li className="panel-empty">Model registry unavailable.</li>}</ul>{models.data?.notes.length ? <p className="performance-provenance">{models.data.notes.join(" · ")}</p> : null}</article>

    {warnings.length ? <aside className="performance-warnings" aria-labelledby="performance-warnings-title"><h3 id="performance-warnings-title">Evidence limitations</h3><ul>{warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></aside> : null}
  </section>;
}

export { PerformanceLab };
