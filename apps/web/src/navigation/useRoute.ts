import { useSyncExternalStore } from "react";
import { flushSync } from "react-dom";

import { taskAwareHref } from "../hooks/useSelectedTaskId";
import { routeByPath, routes } from "./routes";

function readLocation() {
  return `${window.location.pathname}${window.location.search}`;
}

type ViewTransitionDocument = Document & {
  startViewTransition?: (update: () => void) => unknown;
};

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
  navigateTo(path);
}

function navigateTo(path: string) {
  if (path === readLocation()) return;

  const commit = () => {
    window.history.pushState(null, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  };
  const transitionDocument = document as ViewTransitionDocument;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (transitionDocument.startViewTransition && !reducedMotion) {
    transitionDocument.startViewTransition(() => flushSync(commit));
  } else {
    commit();
  }
}

function useRoute() {
  const location = useSyncExternalStore(subscribeToPath, readLocation, () => "/runtime");
  const pathname = location.split("?", 1)[0];
  const activePath = routeByPath.has(pathname) ? pathname : "/runtime";
  return {
    activePath,
    activeRoute: routeByPath.get(activePath) ?? routes[0],
    navigate,
    navigateTo,
    routeHref: taskAwareHref,
  };
}

export { useRoute };
