import { useSyncExternalStore } from "react";

import { taskAwareHref } from "../hooks/useSelectedTaskId";
import { routeByPath, routes } from "./routes";

function readLocation() {
  return `${window.location.pathname}${window.location.search}`;
}

function subscribeToPath(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  return () => window.removeEventListener("popstate", onChange);
}

function navigate(event: React.MouseEvent<HTMLAnchorElement>, path: string) {
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  ) {
    return;
  }

  event.preventDefault();
  window.history.pushState(null, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function useRoute() {
  const location = useSyncExternalStore(subscribeToPath, readLocation, () => "/runtime");
  const pathname = location.split("?", 1)[0];
  const activePath = routeByPath.has(pathname) ? pathname : "/runtime";
  return {
    activePath,
    activeRoute: routeByPath.get(activePath) ?? routes[0],
    navigate,
    routeHref: taskAwareHref,
  };
}

export { useRoute };
