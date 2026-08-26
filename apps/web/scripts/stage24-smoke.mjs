import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE24_WEB_BASE ?? "http://127.0.0.1:4173";
const routes = ["/runtime", "/agents", "/traces", "/hardware", "/chaos", "/security"];

async function timedFetch(endpoint) {
  const startedAt = performance.now();
  const response = await fetch(`${baseUrl}${endpoint}`);
  const body = await response.text();
  return {
    endpoint,
    status: response.status,
    content_type: response.headers.get("content-type"),
    elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
    body,
  };
}

const startedAt = performance.now();
const [routeResponses, paletteModule, interactionStyles, healthResponse] = await Promise.all([
  Promise.all(routes.map(timedFetch)),
  timedFetch("/src/components/interaction/CommandPalette.tsx"),
  timedFetch("/src/styles/interaction.css"),
  timedFetch("/v1/health"),
]);

const healthPayload = JSON.parse(healthResponse.body);
const routeTimes = routeResponses.map((response) => response.elapsed_ms).sort((a, b) => a - b);
const result = {
  stage: 24,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: {
    route_statuses: Object.fromEntries(routeResponses.map((response) => [response.endpoint, response.status])),
    route_retrieval_ms: {
      minimum: routeTimes[0],
      median: routeTimes[Math.floor(routeTimes.length / 2)],
      maximum: routeTimes.at(-1),
    },
    command_palette_module_status: paletteModule.status,
    interaction_styles_status: interactionStyles.status,
    command_palette_contract_present: paletteModule.body.includes("Go to a workspace")
      && paletteModule.body.includes("Matching workspaces"),
    native_view_transition_contract_present: interactionStyles.body.includes("view-transition")
      || interactionStyles.body.includes("command-modal-in"),
  },
  backend: {
    health_status: healthResponse.status,
    runtime_status: healthPayload.data?.runtime_status,
    integrity: healthPayload.data?.persistence?.integrity,
    health_retrieval_ms: healthResponse.elapsed_ms,
  },
  elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
};

if (
  routeResponses.some((response) => response.status !== 200 || !response.body.includes('id="root"'))
  || paletteModule.status !== 200
  || interactionStyles.status !== 200
  || !result.frontend.command_palette_contract_present
  || !result.frontend.native_view_transition_contract_present
  || healthResponse.status !== 200
  || result.backend.runtime_status !== "running"
  || result.backend.integrity !== "ok"
) throw new Error(`Stage 24 smoke criteria failed: ${JSON.stringify(result)}`);

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage24-interaction-motion-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
