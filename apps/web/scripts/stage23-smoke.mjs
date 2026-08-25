import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const baseUrl = process.env.STAGE23_WEB_BASE ?? "http://127.0.0.1:4173";

async function envelope(endpoint, init) {
  const response = await fetch(`${baseUrl}${endpoint}`, init);
  const payload = await response.json();
  if (!response.ok || typeof payload !== "object" || payload === null || !("data" in payload)) {
    throw new Error(`${endpoint} failed with HTTP ${response.status}`);
  }
  return { status: response.status, data: payload.data };
}

const startedAt = performance.now();
const [chaosRoute, securityRoute] = await Promise.all([fetch(`${baseUrl}/chaos`), fetch(`${baseUrl}/security`)]);
const catalogsStarted = performance.now();
const [chaosCatalog, securityCatalog] = await Promise.all([envelope("/v1/chaos"), envelope("/v1/security")]);
const catalogsMs = performance.now() - catalogsStarted;

const chaosSelection = ["model-timeout", "database-result-failure", "agent-crash-recovery"];
const chaosStarted = performance.now();
const chaos = await envelope("/v1/chaos", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ confirm: true, scenarios: chaosSelection }),
});
const chaosHttpMs = performance.now() - chaosStarted;

const securitySelection = securityCatalog.data.cases.map((item) => item.case_id);
const securityStarted = performance.now();
const security = await envelope("/v1/security", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ confirm: true, cases: securitySelection }),
});
const securityHttpMs = performance.now() - securityStarted;
const [retained, health] = await Promise.all([envelope("/v1/security/results"), envelope("/v1/health")]);

const chaosRecovery = chaos.data.report.scenarios.find((item) => item.recovery.attempted);
const persistenceFailure = chaos.data.report.scenarios.find((item) => item.scenario_id === "database-result-failure");
const result = {
  stage: 23,
  captured_at_utc: new Date().toISOString(),
  target: baseUrl,
  frontend: {
    chaos_route_http_status: chaosRoute.status,
    security_route_http_status: securityRoute.status,
    api_proxy_verified: true,
  },
  catalogs: {
    retrieval_ms: Number(catalogsMs.toFixed(3)),
    chaos_scenarios: chaosCatalog.data.scenarios.length,
    chaos_maximum_per_run: chaosCatalog.data.maximum_scenarios_per_run,
    chaos_armed_by_default: chaosCatalog.data.armed_by_default,
    security_cases: securityCatalog.data.cases.length,
    security_maximum_per_run: securityCatalog.data.maximum_cases_per_run,
  },
  chaos: {
    http_ms: Number(chaosHttpMs.toFixed(3)),
    report_duration_ms: chaos.data.report.duration_ms,
    run_id: chaos.data.report.run_id,
    scenarios: chaos.data.report.summary.scenarios,
    injections: chaos.data.report.summary.injections,
    expected_outcomes_met: chaos.data.report.summary.expected_outcomes_met,
    containment_rate_percent: chaos.data.report.summary.containment_rate_percent,
    known_persistence_containment_gap_reproduced: persistenceFailure?.contained === false,
    recovery_attempts: chaos.data.report.summary.recovery_attempts,
    recovery_successes: chaos.data.report.summary.recovery_successes,
    recovery_scenario: chaosRecovery?.scenario_id ?? null,
    recovery_succeeded: chaosRecovery?.recovery.succeeded ?? null,
    added_latency_p95_ms: chaos.data.report.summary.added_latency_ms.p95,
    database_integrity: chaos.data.report.database_integrity,
    real_llm_calls: chaos.data.report.summary.real_llm_calls,
    isolation: chaos.data.isolation,
  },
  security: {
    http_ms: Number(securityHttpMs.toFixed(3)),
    result_id: security.data.result_id,
    cases: security.data.report.summary.cases,
    passed: security.data.report.summary.passed,
    failed: security.data.report.summary.failed,
    pass_rate_percent: security.data.report.summary.pass_rate_percent,
    suite_duration_ms: security.data.report.summary.total_duration_ms,
    database_integrity: security.data.report.summary.integrity_check,
    real_llm_calls: security.data.report.summary.real_llm_calls,
    retained_result_matches: retained.data.result_id === security.data.result_id,
    scope: security.data.scope,
  },
  serving_runtime: { status: health.data.runtime_status, integrity: health.data.persistence.integrity },
  elapsed_ms: Number((performance.now() - startedAt).toFixed(3)),
};

if (
  chaosRoute.status !== 200
  || securityRoute.status !== 200
  || chaosCatalog.data.armed_by_default !== false
  || chaosCatalog.data.scenarios.length !== 9
  || chaosCatalog.data.maximum_scenarios_per_run !== 3
  || securityCatalog.data.cases.length !== 14
  || chaos.data.report.summary.expected_outcomes_met !== chaosSelection.length
  || chaos.data.report.summary.contained !== chaosSelection.length - 1
  || persistenceFailure?.contained !== false
  || chaosRecovery?.recovery.succeeded !== true
  || chaos.data.report.database_integrity !== "ok"
  || chaos.data.report.summary.real_llm_calls !== 0
  || security.data.report.summary.passed !== securitySelection.length
  || security.data.report.summary.failed !== 0
  || security.data.report.summary.integrity_check !== "ok"
  || security.data.report.summary.real_llm_calls !== 0
  || retained.data.result_id !== security.data.result_id
  || health.data.runtime_status !== "running"
) throw new Error(`Stage 23 smoke criteria failed: ${JSON.stringify(result)}`);

const timestamp = result.captured_at_utc.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
const outputDirectory = fileURLToPath(new URL("../../../benchmarks/results/", import.meta.url));
await mkdir(outputDirectory, { recursive: true });
const outputPath = path.join(outputDirectory, `stage23-chaos-security-${timestamp}.json`);
await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ ...result, evidence_file: outputPath }, null, 2));
