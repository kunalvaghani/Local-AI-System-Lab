import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const runtimeEnvironment = (globalThis as typeof globalThis & {
  process?: { env?: Record<string, string | undefined> };
}).process?.env ?? {};
const apiTarget = runtimeEnvironment.LOCAL_AI_API_TARGET ?? "http://127.0.0.1:8765";
const configuredPort = Number(runtimeEnvironment.LOCAL_AI_WEB_PORT ?? "4173");
const apiUrl = new URL(apiTarget);
if (!new Set(["127.0.0.1", "localhost", "::1"]).has(apiUrl.hostname)) {
  throw new Error("LOCAL_AI_API_TARGET must remain loopback-only");
}
if (!Number.isInteger(configuredPort) || configuredPort < 1 || configuredPort > 65_535) {
  throw new Error("LOCAL_AI_WEB_PORT must be a valid TCP port");
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: configuredPort,
    strictPort: true,
    proxy: {
      "/v1": apiTarget,
    },
  },
  preview: {
    host: "127.0.0.1",
    port: configuredPort,
    strictPort: true,
    proxy: {
      "/v1": apiTarget,
    },
  },
  build: {
    target: "es2022",
    sourcemap: true,
  },
});
