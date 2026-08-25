type RouteGroup = "Observe" | "Investigate" | "Test" | "System";

type RouteDefinition = {
  path: string;
  label: string;
  shortLabel: string;
  purpose: string;
  endpoint: string;
  group: RouteGroup;
};

const routeGroups: readonly RouteGroup[] = ["Observe", "Investigate", "Test", "System"];

const routes: readonly RouteDefinition[] = [
  { path: "/runtime", label: "Runtime", shortLabel: "RT", purpose: "Command center and live execution overview", endpoint: "/v1/health", group: "Observe" },
  { path: "/tasks", label: "Tasks", shortLabel: "TK", purpose: "Task lifecycle, outputs, and evidence", endpoint: "/v1/tasks/{task_id}", group: "Observe" },
  { path: "/agents", label: "Agents", shortLabel: "AG", purpose: "Registered agent roles and states", endpoint: "/v1/agents", group: "Observe" },
  { path: "/scheduler", label: "Scheduler", shortLabel: "SQ", purpose: "Queue order, priority, and admission", endpoint: "/v1/scheduler", group: "Observe" },
  { path: "/models", label: "Models", shortLabel: "MD", purpose: "Model registry, profiles, and budgets", endpoint: "/v1/models", group: "Investigate" },
  { path: "/hardware", label: "Hardware", shortLabel: "HW", purpose: "Measured resource capacity and pressure", endpoint: "/v1/hardware", group: "Investigate" },
  { path: "/traces", label: "Traces & Replay", shortLabel: "TR", purpose: "Execution evidence and deterministic replay", endpoint: "/v1/traces/{run_id}", group: "Investigate" },
  { path: "/metrics", label: "Metrics", shortLabel: "MX", purpose: "Latency, throughput, and resource telemetry", endpoint: "/v1/metrics", group: "Investigate" },
  { path: "/chaos", label: "Chaos Lab", shortLabel: "CH", purpose: "Controlled fault experiments and recovery", endpoint: "/v1/chaos", group: "Test" },
  { path: "/security", label: "Security", shortLabel: "SE", purpose: "Adversarial test evidence, not certification", endpoint: "/v1/security/results", group: "Test" },
  { path: "/design-system", label: "Design System", shortLabel: "DS", purpose: "Stage 18 tokens, states, and components", endpoint: "Local prototype", group: "System" },
  { path: "/settings", label: "Settings", shortLabel: "ST", purpose: "Local preferences and build information", endpoint: "Device local", group: "System" },
] as const;

const routeByPath = new Map(routes.map((route) => [route.path, route]));

export { routeByPath, routeGroups, routes };
export type { RouteDefinition, RouteGroup };
