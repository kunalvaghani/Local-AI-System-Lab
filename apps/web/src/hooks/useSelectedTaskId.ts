import { useCallback, useSyncExternalStore } from "react";

const TASK_ID_PATTERN = /^[A-Za-z0-9-]{1,128}$/;

function currentTaskId() {
  const value = new URLSearchParams(window.location.search).get("task");
  return value && TASK_ID_PATTERN.test(value) ? value : null;
}

function subscribe(callback: () => void) {
  window.addEventListener("popstate", callback);
  return () => window.removeEventListener("popstate", callback);
}

function useSelectedTaskId() {
  const taskId = useSyncExternalStore(subscribe, currentTaskId, () => null);
  const selectTask = useCallback((nextTaskId: string | null, replace = false) => {
    const url = new URL(window.location.href);
    if (nextTaskId && TASK_ID_PATTERN.test(nextTaskId)) {
      url.searchParams.set("task", nextTaskId);
    } else {
      url.searchParams.delete("task");
    }
    window.history[replace ? "replaceState" : "pushState"](null, "", `${url.pathname}${url.search}${url.hash}`);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  return { taskId, selectTask };
}

export { useSelectedTaskId };
