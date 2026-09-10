#!/usr/bin/env node
/**
 * npm start — same stand as `python scripts/run_review_shell.py`.
 * API + Vite. Not the jury CLI. Not vite-only (`npm run dev` stays smoke/dev).
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const windowsPython = resolve(repoRoot, "backend", ".venv", "Scripts", "python.exe");
const posixPython = resolve(repoRoot, "backend", ".venv", "bin", "python");
const python = existsSync(windowsPython)
  ? windowsPython
  : existsSync(posixPython)
    ? posixPython
    : null;

if (python === null) {
  process.stderr.write(
    "backend/.venv not found. From AeroBIM/backend: py -3.12 -m venv .venv && pip install -e \".[dev,raster]\"\n",
  );
  process.exit(1);
}

const child = spawn(python, ["-m", "aerobim.tools.run_it_mentor_stand", ...process.argv.slice(2)], {
  cwd: repoRoot,
  stdio: "inherit",
  windowsHide: false,
});
child.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
