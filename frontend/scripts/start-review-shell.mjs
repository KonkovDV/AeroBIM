#!/usr/bin/env node
/**
 * npm start — same stand as `python scripts/run_review_shell.py`.
 * API + Vite on 8080 / 5173. Not Next.js. Not the jury CLI.
 * `npm run dev` stays Vite-only (needs the API already up).
 *
 * If this frontend tree was copied without backend, set AEROBIM_BACKEND_DIR
 * to the clone's backend directory (not a /tmp-only copy of the UI).
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoRoot = resolve(frontendDir, "..");
const backendDir = process.env.AEROBIM_BACKEND_DIR
  ? resolve(process.env.AEROBIM_BACKEND_DIR)
  : resolve(repoRoot, "backend");
const windowsPython = resolve(backendDir, ".venv", "Scripts", "python.exe");
const posixPython = resolve(backendDir, ".venv", "bin", "python");
const python = existsSync(windowsPython)
  ? windowsPython
  : existsSync(posixPython)
    ? posixPython
    : null;

if (python === null) {
  process.stderr.write(
    `backend/.venv not found under ${backendDir}. ` +
      "AeroBIM API lives in <clone>/backend " +
      "(Windows: .venv\\Scripts\\python.exe; Linux: .venv/bin/python), " +
      "not a frontend-only tree. Set AEROBIM_BACKEND_DIR if the backend is elsewhere. " +
      'From that directory: py -3.12 -m venv .venv && .venv\\Scripts\\python.exe -m pip install -e ".[dev,raster]"\n',
  );
  process.exit(1);
}

const child = spawn(python, ["-m", "aerobim.tools.run_review_stand", ...process.argv.slice(2)], {
  cwd: backendDir,
  env: {
    ...process.env,
    AEROBIM_BACKEND_DIR: backendDir,
    AEROBIM_FRONTEND_DIR: frontendDir,
    AEROBIM_PROXY_TARGET: process.env.AEROBIM_PROXY_TARGET || "http://127.0.0.1:8080",
  },
  stdio: "inherit",
  windowsHide: false,
});
child.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
