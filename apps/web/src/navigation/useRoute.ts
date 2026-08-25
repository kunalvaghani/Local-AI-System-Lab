import { useSyncExternalStore } from "react";

import { routeByPath, routes } from "./routes";

function readPath() {
  const path = window.location.pathname;
  return routeByPath.has(path) ? path : "/runtime";
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
  const activePath = useSyncExternalStore(subscribeToPath, readPath, () => "/runtime");
  return {
    activePath,
    activeRoute: routeByPath.get(activePath) ?? routes[0],
    navigate,
  };
}

export { useRoute };
