"""Generate audit/evidence/audit-baseline.json — measurement only."""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(cmd: str, *, cwd: Path | None = None) -> dict[str, object]:
    proc = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": cmd,
        "cwd": str(cwd or ROOT),
        "exit_code": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }


def loc(root: Path, suffixes: tuple[str, ...]) -> dict[str, int]:
    files = 0
    lines = 0
    skip = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "dist"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in skip for part in path.parts):
            continue
        files += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines += text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    return {"files": files, "lines": lines}


def optional_import(module: str) -> dict[str, object]:
    result = run(f'{sys.executable} -c "import {module}"')
    return {
        "module": module,
        "importable": result["exit_code"] == 0,
        "command": result["command"],
        "exit_code": result["exit_code"],
        "stderr": result["stderr"][-500:],
    }


def main() -> None:
    evidence_dir = ROOT / "audit" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    git_sha = run("git rev-parse HEAD")
    git_branch = run("git branch --show-current")
    git_status = run("git status --porcelain")
    git_log = run("git log -1 --format=%H%n%ci%n%s")
    py_ver = run(f"{sys.executable} --version")
    node_ver = run("node --version")
    npm_ver = run("npm --version")
    collect = run(f"{sys.executable} -m pytest --collect-only -q", cwd=ROOT / "backend")
    pytest_run = run(f"{sys.executable} -m pytest -q --tb=no", cwd=ROOT / "backend")
    pip_freeze = run(f"{sys.executable} -m pip freeze")
    frontend_test = run("npm test", cwd=ROOT / "frontend")

    dirty_lines = [line for line in str(git_status["stdout"]).splitlines() if line.strip()]
    collect_out = str(collect["stdout"])
    collected_match = re.search(r"(\d+) tests? collected", collect_out)
    pytest_out = str(pytest_run["stdout"]).replace("\x00", "")
    pytest_match = re.search(
        r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?(?:, (\d+) errors?)?",
        pytest_out,
    )

    key_pkgs = [
        "fastapi",
        "uvicorn",
        "ifcopenshell",
        "ifctester",
        "pymupdf",
        "PyJWT",
        "redis",
        "SQLAlchemy",
        "httpx",
        "pytest",
        "ruff",
        "mypy",
        "starlette",
        "python-multipart",
    ]
    installed: dict[str, str | None] = {}
    freeze_lines = str(pip_freeze["stdout"]).splitlines()
    freeze_map = {}
    for line in freeze_lines:
        if "==" in line:
            name, _, ver = line.partition("==")
            freeze_map[name.lower()] = ver
    for pkg in key_pkgs:
        installed[pkg] = freeze_map.get(pkg.lower())

    optional = {
        "ifcclash": optional_import("ifcclash"),
        "rapidocr": optional_import("rapidocr"),
        "onnxruntime": optional_import("onnxruntime"),
        "boto3": optional_import("boto3"),
        "docling": optional_import("docling"),
    }

    # API endpoints from source grep-equivalent
    api_path = ROOT / "backend" / "src" / "aerobim" / "presentation" / "http" / "api.py"
    api_text = api_path.read_text(encoding="utf-8")
    endpoints = re.findall(r'@app\.(get|post|put|delete|patch)\("([^"]+)"', api_text)

    pyproject = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    cli_scripts = re.findall(r'^aerobim-[\w-]+\s*=\s*"[^"]+"', pyproject, flags=re.M)
    # Also tools with __main__
    tools_dir = ROOT / "backend" / "src" / "aerobim" / "tools"
    tool_mains = sorted(p.name for p in tools_dir.glob("*.py") if p.name != "__init__.py")

    frontend_routes = [
        "SPA single-page App.tsx (no react-router routes found in inventory)",
        "components: IfcViewerPanel, DrawingEvidencePanel",
    ]

    docker = {
        "files_present": [
            str(p.relative_to(ROOT)).replace("\\", "/")
            for p in [
                ROOT / "docker-compose.yml",
                ROOT / "backend" / "Dockerfile",
            ]
            if p.exists()
        ],
        "compose_services": [],
    }
    compose = ROOT / "docker-compose.yml"
    if compose.exists():
        for line in compose.read_text(encoding="utf-8").splitlines():
            if line.endswith(":") and not line.startswith(" ") and line.strip() != "services:":
                continue
            m = re.match(r"^  ([a-zA-Z0-9_-]+):\s*$", line)
            if m:
                docker["compose_services"].append(m.group(1))

    ci_runs = run("gh run list --limit 5 --json conclusion,status,name,headBranch,databaseId,createdAt,displayTitle")

    baseline = {
        "artifact_type": "aerobim_red_team_audit_baseline",
        "schema_version": "1.0.0",
        "audit_date_utc": datetime.now(tz=UTC).isoformat(),
        "author_relationship": "self",
        "note": (
            "Independent Red Team inventory. Values are command-derived. "
            "Working tree may be dirty relative to committed SHA."
        ),
        "git": {
            "commit_sha": str(git_sha["stdout"]),
            "branch": str(git_branch["stdout"]),
            "latest_commit": str(git_log["stdout"]),
            "dirty": bool(dirty_lines),
            "uncommitted_change_count": len(dirty_lines),
            "uncommitted_paths": dirty_lines,
        },
        "environment": {
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "platform": platform.platform(),
            },
            "python": str(py_ver["stdout"]),
            "python_full": sys.version,
            "node": str(node_ver["stdout"]),
            "npm": str(npm_ver["stdout"]),
        },
        "loc": {
            "backend_src_py": loc(ROOT / "backend" / "src", (".py",)),
            "backend_tests_py": loc(ROOT / "backend" / "tests", (".py",)),
            "frontend_src": loc(ROOT / "frontend" / "src", (".ts", ".tsx", ".css")),
            "docs_md": loc(ROOT / "docs", (".md",)),
            "note": "Excludes node_modules/dist/__pycache__; does NOT count samples or site-packages",
        },
        "tests": {
            "backend_collected": int(collected_match.group(1)) if collected_match else None,
            "backend_passed": int(pytest_match.group(1)) if pytest_match else None,
            "backend_skipped": int(pytest_match.group(2) or 0) if pytest_match else None,
            "backend_failed": int(pytest_match.group(3) or 0) if pytest_match else None,
            "backend_errors": int(pytest_match.group(4) or 0) if pytest_match else None,
            "frontend_npm_test": {
                "exit_code": frontend_test["exit_code"],
                "stdout_tail": str(frontend_test["stdout"])[-1500:],
                "stderr_tail": str(frontend_test["stderr"])[-800:],
            },
        },
        "dependencies": {
            "required_installed_versions": installed,
            "optional_import_probe": optional,
            "optional_groups_declared": ["dev", "raster", "clash", "docling", "enterprise"],
            "pip_freeze_line_count": len(freeze_lines),
            "pip_freeze_path": "audit/evidence/_pip_freeze.txt",
        },
        "ci": {
            "workflows_present": [
                ".github/workflows/ci.yml",
                ".github/workflows/release-readiness.yml",
                ".github/workflows/academic-benchmark-release.yml",
            ],
            "gh_run_list": json.loads(str(ci_runs["stdout"]) or "[]")
            if ci_runs["exit_code"] == 0 and str(ci_runs["stdout"]).startswith("[")
            else {"raw": str(ci_runs["stdout"])[-2000:], "exit_code": ci_runs["exit_code"]},
        },
        "runtime_entrypoints": {
            "http_factory": "backend/src/aerobim/presentation/http/api.py::create_app",
            "di_bootstrap": "backend/src/aerobim/infrastructure/di/bootstrap.py::bootstrap_container",
            "docker": "backend/Dockerfile + docker-compose.yml",
            "api_endpoints": [{"method": m.upper(), "path": p} for m, p in endpoints],
            "cli_project_scripts": cli_scripts,
            "tools_modules": tool_mains,
            "frontend_routes": frontend_routes,
        },
        "commands_executed": {
            "git_sha": git_sha,
            "git_branch": git_branch,
            "git_status": {
                **git_status,
                "stdout": "\n".join(dirty_lines[:80]),
            },
            "pytest_collect": {
                "command": collect["command"],
                "exit_code": collect["exit_code"],
                "stdout_tail": collect_out[-800:],
            },
            "pytest_run": {
                "command": pytest_run["command"],
                "exit_code": pytest_run["exit_code"],
                "stdout_tail": pytest_out[-800:],
            },
        },
    }

    out_path = evidence_dir / "audit-baseline.json"
    out_path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence_dir / "_pip_freeze.txt").write_text(str(pip_freeze["stdout"]) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        json.dumps(
            {
                "sha": baseline["git"]["commit_sha"],
                "dirty": baseline["git"]["dirty"],
                "tests": baseline["tests"],
                "loc": baseline["loc"],
                "optional": {k: v["importable"] for k, v in optional.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
