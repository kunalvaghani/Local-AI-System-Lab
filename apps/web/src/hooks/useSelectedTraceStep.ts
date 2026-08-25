import { useCallback, useSyncExternalStore } from "react";

const STEP_ID_PATTERN = /^[A-Za-z0-9-]{1,128}$/;

function currentStepId() {
  const value = new URLSearchParams(window.location.search).get("step");
  return value && STEP_ID_PATTERN.test(value) ? value : null;
}

function subscribe(callback: () => void) {
  window.addEventListener("popstate", callback);
  return () => window.removeEventListener("popstate", callback);
}

function useSelectedTraceStep() {
  const stepId = useSyncExternalStore(subscribe, currentStepId, () => null);
  const selectStep = useCallback((nextStepId: string | null) => {
    const url = new URL(window.location.href);
    if (nextStepId && STEP_ID_PATTERN.test(nextStepId)) url.searchParams.set("step", nextStepId);
    else url.searchParams.delete("step");
    window.history.pushState(null, "", `${url.pathname}${url.search}${url.hash}`);
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);
  return { stepId, selectStep };
}

export { useSelectedTraceStep };
