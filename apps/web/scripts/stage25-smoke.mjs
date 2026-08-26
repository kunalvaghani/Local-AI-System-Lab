import { gzipSync } from "node:zlib";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE25_WEB_BASE ?? "http://127.0.0.1:4173";
const routes = [
  "/runtime", "/tasks", "/agents", "/scheduler", "/models", "/hardware",
  "/traces", "/metrics", "/chaos", "/security", "/design-system", "/settings",
];
const webRoot = fileURLToPath(new URL("../", import.meta.url));

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

function parseHex(hex) {
  const value = hex.replace("#", "");
  const channels = value.length === 3
    ? value.split("").map((channel) => Number.parseInt(channel + channel, 16))
    : [value.slice(0, 2), value.slice(2, 4), value.slice(4, 6)].map((channel) => Number.parseInt(channel, 16));
  return channels.map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
  });
}

function luminance(hex) {
  const [red, green, blue] = parseHex(hex);
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground, background) {
  const [lighter, darker] = [luminance(foreground), luminance(background)].sort((left, right) => right - left);
  return Number(((lighter + 0.05) / (darker + 0.05)).toFixed(2));
}

function readTokens(source) {
  return Object.fromEntries([...source.matchAll(/(--[a-z0-9-]+):\s*(#[0-9a-f]{6})/gi)].map((match) => [match[1], match[2]]));
}

const startedAt = performance.now();
const [routeResponses, healthResponse, tokenSource, globalStyles, runtimeStyles, eventHook] = await Promise.all([
  Promise.all(routes.map(timedFetch)),
  timedFetch("/v1/health"),
  readFile(path.join(webRoot, "src/styles/tokens.css"), "utf8"),
  readFile(path.join(webRoot, "src/styles/global.css"), "utf8"),
  readFile(path.join(webRoot, "src/styles/runtime.css"), "utf8"),
  readFile(path.join(webRoot, "src/hooks/useTaskEvents.ts"), "utf8"),
]);
const healthPayload = JSON.parse(healthResponse.body);
const routeTimes = routeResponses.map((response) => response.elapsed_ms).sort((left, right) => left - right);
const tokens = readTokens(tokenSource);
const contrastPairs = [
  ["primary-on-canvas", "--color-text", "--color-canvas", 4.5],
  ["muted-on-canvas", "--color-text-muted", "--color-canvas", 4.5],
  ["faint-on-canvas", "--color-text-faint", "--color-canvas", 4.5],
  ["faint-on-panel", "--color-text-faint", "--color-surface-1", 4.5],
  ["accent-on-soft", "--color-accent", "--color-accent-soft", 4.5],
  ["positive-on-panel", "--color-positive", "--color-surface-1", 4.5],
  ["warning-on-panel", "--color-warning", "--color-surface-1", 4.5],
  ["critical-on-panel", "--color-critical", "--color-surface-1", 4.5],
  ["focus-on-canvas", "--color-focus", "--color-canvas", 3],
].map(([name, foreground, background, minimum]) => ({
  name,
  foreground: tokens[foreground],
  background: tokens[background],
  minimum,
  ratio: contrastRatio(tokens[foreground], tokens[background]),
}));

const assetDirectory = path.join(webRoot, "dist/assets");
const assetFiles = await readdir(assetDirectory);
const javascriptFiles = assetFiles.filter((file) => path.extname(file) === ".js");
let compressedJavascriptBytes = 0;
for (const file of javascriptFiles) {
  compressedJavascriptBytes += gzipSync(await readFile(path.join(assetDirectory, file))).byteLength;
}

const result = {
  stage: 25,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: {
    route_statuses: Object.fromEntries(routeResponses.map((response) => [response.endpoint, response.status])),
    route_retrieval_ms: {
      minimum: routeTimes[0],
      median: routeTimes[Math.floor(routeTimes.length / 2)],
      maximum: routeTimes.at(-1),
    },
    javascript_files: javascriptFiles.length,
    javascript_gzip_bytes: compressedJavascriptBytes,
    javascript_budget_bytes: 250 * 1024,
  },
  accessibility: {
    contrast_pairs: contrastPairs,
    reduced_motion_contract_present: globalStyles.includes("prefers-reduced-motion: reduce"),
    minimum_width_floor_removed: globalStyles.includes("min-width: 0"),
    container_reflow_contract_present: runtimeStyles.includes("@container runtime"),
  },
  performance: {
    stream_frame_batching_present: eventHook.includes("requestAnimationFrame(flushPendingEvents)"),
    stream_retention_bound_present: eventHook.includes("merged.slice(-200)"),
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
  || compressedJavascriptBytes > result.frontend.javascript_budget_bytes
  || contrastPairs.some((pair) => pair.ratio < pair.minimum)
  || !Object.values(result.accessibility).every((value) => value === true || Array.isArray(value))
  || !Object.values(result.performance).every(Boolean)
  || healthResponse.status !== 200
  || result.backend.runtime_status !== "running"
  || result.backend.integrity !== "ok"
) throw new Error(`Stage 25 smoke criteria failed: ${JSON.stringify(result)}`);

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage25-responsive-accessibility-performance-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
