import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./styles/tokens.css";
import "./styles/global.css";
import "./styles/runtime.css";
import "./styles/scheduler.css";
import "./styles/agents.css";
import "./styles/traces.css";
import "./styles/performance.css";
import "./styles/chaos-security.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Application root is unavailable");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
