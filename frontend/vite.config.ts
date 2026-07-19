import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

/**
 * Dev auth proxy: browser calls same-origin `/v1/*`; Vite injects
 * `Authorization: Bearer …` from **non-VITE** `AEROBIM_API_BEARER_TOKEN`
 * so the secret never ships in the JS bundle.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backend = (env.AEROBIM_PROXY_TARGET || "http://127.0.0.1:8080").replace(/\/$/, "");
  const bearer = (env.AEROBIM_API_BEARER_TOKEN || "").trim();

  return {
    plugins: [react()],
    build: {
      chunkSizeWarningLimit: 700,
      rollupOptions: {
        output: {
          manualChunks(id: string) {
            if (/[\\/]node_modules[\\/]web-ifc[\\/]/.test(id)) {
              return "vendor-web-ifc";
            }
            if (/[\\/]node_modules[\\/]three[\\/]/.test(id)) {
              return "vendor-three";
            }
            return undefined;
          },
        },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      // Unit suite stays free of Playwright; browser smoke is `npm run smoke:browser`.
      include: ["src/**/*.{test,spec}.{ts,tsx}", "scripts/**/*.test.mjs"],
      exclude: ["**/node_modules/**", "**/dist/**"],
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/v1": {
          target: backend,
          changeOrigin: true,
          configure: (proxy) => {
            proxy.on("proxyReq", (proxyReq) => {
              if (bearer) {
                proxyReq.setHeader("Authorization", `Bearer ${bearer}`);
              }
            });
          },
        },
        "/health": {
          target: backend,
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: 4173,
    },
  };
});
