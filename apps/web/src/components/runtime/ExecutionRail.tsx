import type { LifecycleEvent, LifecycleEventData } from "../../api/types";
import type { StreamState } from "../../hooks/useTaskEvents";
import { StatusToken } from "../StatusToken";

type ExecutionRailProps = {
  events: LifecycleEvent[];
  streamState: StreamState;
};

function eventLabel(event: LifecycleEvent) {
  if (event.event === "lifecycle") return (event.data as LifecycleEventData).name;
  if (event.event === "task") return "task.snapshot";
  return `stream.${String((event.data as { reason?: unknown }).reason ?? "ended")}`;
}

function eventState(event: LifecycleEvent) {
  return event.event === "lifecycle" ? (event.data as LifecycleEventData).state : null;
}

function eventTime(event: LifecycleEvent) {
  if (event.event !== "lifecycle") return null;
  const value = (event.data as LifecycleEventData).recorded_at_utc;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toLocaleTimeString();
}

function ExecutionRail({ events, streamState }: ExecutionRailProps) {
  const visible = events.filter((event) => event.event === "lifecycle").slice(-30);
  return (
    <article className="execution-rail" aria-labelledby="execution-rail-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">Ordered SSE</p><h3 id="execution-rail-title">Execution rail</h3></div>
        <StatusToken tone={streamState === "live" ? "active" : streamState === "error" ? "critical" : streamState === "closed" ? "healthy" : "queued"}>{streamState}</StatusToken>
      </div>
      {visible.length === 0 ? <p className="panel-empty">Lifecycle evidence will appear when a selected task runs.</p> : (
        <ol className="event-list">
          {visible.map((event) => (
            <li key={`${event.event}-${event.id}`}>
              <span>{event.id}</span>
              <div><strong>{eventLabel(event)}</strong><small>{eventState(event) ?? "event"}</small></div>
              <time>{eventTime(event) ?? "—"}</time>
            </li>
          ))}
        </ol>
      )}
      <small className="evidence-note">Showing the latest {visible.length} of {events.filter((event) => event.event === "lifecycle").length} lifecycle events; the client retains at most 200 per selected task.</small>
    </article>
  );
}

export { ExecutionRail };
