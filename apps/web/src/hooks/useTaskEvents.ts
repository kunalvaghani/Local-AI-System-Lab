import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import type {
  LifecycleEvent,
  LifecycleEventData,
  StreamEndData,
  TaskRecord,
} from "../api/types";
import { queryKeys } from "../query/runtimeQueries";

type StreamState = "idle" | "connecting" | "live" | "closed" | "error";

function parseObject(value: string): Record<string, unknown> | null {
  try {
    const parsed: unknown = JSON.parse(value);
    return typeof parsed === "object" && parsed !== null && !Array.isArray(parsed)
      ? parsed as Record<string, unknown>
      : null;
  } catch {
    return null;
  }
}

function useTaskEvents(taskId: string | null, terminal: boolean) {
  const queryClient = useQueryClient();
  const [events, setEvents] = useState<LifecycleEvent[]>([]);
  const [state, setState] = useState<StreamState>(taskId ? "connecting" : "idle");

  useEffect(() => {
    setEvents([]);
    setState(taskId ? "connecting" : "idle");
  }, [taskId]);

  useEffect(() => {
    if (taskId && terminal) setState("closed");
    if (!taskId || terminal) {
      return undefined;
    }

    let source: EventSource | null = null;
    let reconnectTimer: number | null = null;
    let disposed = false;
    let cursor = 0;

    const append = (event: LifecycleEvent) => {
      cursor = Math.max(cursor, Number.parseInt(event.id, 10) || cursor);
      setEvents((current) => {
        if (current.some((item) => item.id === event.id && item.event === event.event)) {
          return current;
        }
        return [...current, event].slice(-200);
      });
    };

    const connect = () => {
      if (disposed) return;
      setState("connecting");
      source = new EventSource(`/v1/tasks/${encodeURIComponent(taskId)}/events?after=${cursor}`);
      source.onopen = () => setState("live");

      source.addEventListener("lifecycle", (raw) => {
        const message = raw as MessageEvent<string>;
        const data = parseObject(message.data);
        if (data) append({ id: message.lastEventId, event: "lifecycle", data: data as LifecycleEventData });
      });

      source.addEventListener("task", (raw) => {
        const message = raw as MessageEvent<string>;
        const data = parseObject(message.data);
        if (!data) return;
        const task = data as TaskRecord;
        append({ id: message.lastEventId, event: "task", data: task });
        queryClient.setQueryData(queryKeys.task(taskId), task);
      });

      source.addEventListener("end", (raw) => {
        const message = raw as MessageEvent<string>;
        const data = parseObject(message.data);
        if (!data) return;
        const end = data as StreamEndData;
        append({ id: message.lastEventId, event: "end", data: end });
        source?.close();
        if (end.task_continues && !disposed) {
          reconnectTimer = window.setTimeout(connect, 250);
        } else {
          setState("closed");
          void queryClient.invalidateQueries({ queryKey: queryKeys.task(taskId) });
          void queryClient.invalidateQueries({ queryKey: ["runtime"] });
        }
      });

      source.onerror = () => {
        source?.close();
        if (!disposed) setState("error");
      };
    };

    connect();
    return () => {
      disposed = true;
      source?.close();
      if (reconnectTimer !== null) window.clearTimeout(reconnectTimer);
    };
  }, [queryClient, taskId, terminal]);

  return { events, state };
}

export { useTaskEvents };
export type { StreamState };
