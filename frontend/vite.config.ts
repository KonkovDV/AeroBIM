import type { ClientRequest } from "node:http";
import { cwd } from "node:process";
import react from "@vitejs/plugin-react";
import { loadEnv, type Plugin } from "vite";
import { defineConfig } from "vitest/config";
import { requestShouldSkipViteBearer } from "./src/lib/bff-cookie";

const SHELL_SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
} as const;

/** Dev-only: Vite injects CSS as a `<style>` tag. Production `index.html` keeps style-src 'self' (hashed CSS file). */
const DEV_CSP =
  "default-src 'self'; script-src 'self' 'unsafe-eval' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self' ws: wss: http://127.0.0.1:* http://localhost:*; font-src 'self'; worker-src 'self' blob:; child-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'";

function aerobimHtmlSecurity(): Plugin {
  return {
    name: "aerobim-html-security",
    transformIndexHtml(html, ctx) {
      if (!ctx.server) {
        return html;
      }
      return html.replace(
        /(<meta\s+http-equiv="Content-Security-Policy"\s+content=")([^"]*)("\s*\/>)/,
        `$1${DEV_CSP}$3`,
      );
    },
  };
}

/**
 * Dev auth proxy: browser calls same-origin `/v1/*`; Vite injects
 * `Authorization: Bearer …` from **non-VITE** `AEROBIM_API_BEARER_TOKEN`
 * so the secret never ships in the JS bundle.
 */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, cwd(), "");
  const backend = (env.AEROBIM_PROXY_TARGET || "http://127.0.0.1:8080").replace(/\/$/, "");
  const bearer = (env.AEROBIM_API_BEARER_TOKEN || "").trim();

  return {
    plugins: [react(), aerobimHtmlSecurity()],
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
      environmentOptions: {
        jsdom: {
          url: "http://localhost/",
        },
      },
      setupFiles: "./src/test/setup.ts",
      // Same-origin is the shape the unit suite asserts. Without pinning it, a
      // shell that exports VITE_AEROBIM_API_BASE_URL for a local stack turns
      // relative hrefs absolute and reds the suite for environment reasons.
      env: { VITE_AEROBIM_API_BASE_URL: "" },
      // Unit suite stays free of Playwright; browser smoke is `npm run smoke:browser`.
      include: ["src/**/*.{test,spec}.{ts,tsx}", "scripts/**/*.test.mjs"],
      exclude: ["**/node_modules/**", "**/dist/**"],
    },
    server: {
      host: env.AEROBIM_VITE_HOST || "127.0.0.1",
      port: 5173,
      watch: {
        // Smoke and exports write under frontend/artifacts; a page reload
        // mid-demo is worse than a stale artifact on disk.
        ignored: ["**/artifacts/**"],
      },
      headers: { ...SHELL_SECURITY_HEADERS },
      proxy: {
        "/v1": {
          target: backend,
          changeOrigin: true,
          configure: (proxy) => {
            // Some http-proxy type packs omit EventEmitter methods on ProxyServer.
            // RT A12: only inject bearer when the Vite host is loopback.
            const viteHost = (env.AEROBIM_VITE_HOST || "127.0.0.1").trim().toLowerCase();
            const loopback =
              viteHost === "127.0.0.1" ||
              viteHost === "localhost" ||
              viteHost === "::1" ||
              viteHost === "[::1]";
            proxy.on("proxyReq", (proxyReq: ClientRequest) => {
              const cookieHeader = proxyReq.getHeader("cookie");
              const cookieText =
                typeof cookieHeader === "number" ? String(cookieHeader) : cookieHeader;
              if (bearer && loopback && !requestShouldSkipViteBearer(cookieText)) {
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
      host: env.AEROBIM_VITE_HOST || "127.0.0.1",
      port: 4173,
      headers: { ...SHELL_SECURITY_HEADERS },
    },
  };
});
