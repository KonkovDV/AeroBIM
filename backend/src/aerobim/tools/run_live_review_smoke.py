from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, build_opener, urlopen

from aerobim.tools.seed_smoke_report import (
    SMOKE_TENANT_ID,
    build_cli_payload,
    repo_root,
    seed_smoke_report,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORTS = (8080, 8081)
DEFAULT_FRONTEND_PORTS = (5173, 3000, 4173)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}


def backend_dir() -> Path:
    return repo_root() / "backend"


def frontend_dir() -> Path:
    return repo_root() / "frontend"


def default_storage_dir() -> Path:
    return backend_dir() / "var" / "reports-live-review-smoke"


def default_output_dir() -> Path:
    return frontend_dir() / "artifacts" / "browser-smoke-auto"


def backend_python_executable() -> Path:
    candidates = (
        backend_dir() / ".venv" / "Scripts" / "python.exe",
        backend_dir() / ".venv" / "bin" / "python",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("AeroBIM backend virtualenv python executable was not found")


def choose_available_port(host: str, preferred_ports: tuple[int, ...]) -> int:
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if probe.connect_ex((host, port)) != 0:
                return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])


def build_backend_env(
    base_env: Mapping[str, str],
    storage_dir: Path,
    port: int,
    frontend_origin: str,
    tenant_id: str = SMOKE_TENANT_ID,
    host: str = "127.0.0.1",
) -> dict[str, str]:
    """Env for the throwaway rehearsal backend. Development only.

    The page is served with ``VITE_AEROBIM_API_BASE_URL``, so it calls the
    backend directly and no Vite proxy injects ``Authorization``. Anonymous dev
    access is therefore the only way the stack can answer, and an inherited
    ``AEROBIM_API_BEARER_TOKEN`` would switch that branch off and return 401.
    """

    env = dict(base_env)
    env.pop("AEROBIM_API_BEARER_TOKEN", None)
    # Inherited pilot/production signoff must not ride in on a mentor laptop.
    env.pop("AEROBIM_SIGNOFF_PROFILE", None)
    env["AEROBIM_STORAGE_DIR"] = str(storage_dir)
    env["AEROBIM_HOST"] = host
    env["AEROBIM_PORT"] = str(port)
    env["AEROBIM_DEBUG"] = "true"
    env["AEROBIM_CORS_ORIGINS"] = frontend_origin
    env["AEROBIM_ENV"] = "development"
    env["AEROBIM_SIGNOFF_PROFILE"] = "development"
    env["AEROBIM_ALLOW_ANONYMOUS_DEV"] = "true"
    # Must equal the tenant stamped on the seeded report, or «Проекты» is empty.
    env["AEROBIM_API_TENANT_ID"] = tenant_id
    env["AEROBIM_PRIORITY_PROFILE"] = "samolet"
    env["AEROBIM_REMARK_LOCALE"] = "ru"
    return env


def build_frontend_env(base_env: Mapping[str, str], backend_base_url: str) -> dict[str, str]:
    env = dict(base_env)
    env["VITE_AEROBIM_API_BASE_URL"] = backend_base_url
    # Same-origin /v1 and /health on the Vite origin must hit THIS backend,
    # not a leftover process on the default 8080 proxy target.
    env["AEROBIM_PROXY_TARGET"] = backend_base_url
    # Cursor Agent sessions pin PLAYWRIGHT_BROWSERS_PATH at a TEMP sandbox
    # cache. That directory vanishes; the rehearsal must use the user cache.
    env.pop("PLAYWRIGHT_BROWSERS_PATH", None)
    return env


def extract_json_payload(raw_output: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    candidate: dict[str, object] | None = None
    for index, char in enumerate(raw_output):
        if char != "{":
            continue
        try:
            payload, _end_index = decoder.raw_decode(raw_output[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if "trace" in payload and "screenshots" in payload:
            candidate = payload

    if candidate is None:
        raise ValueError("No JSON payload found in smoke command output")
    return candidate


def extract_demo_payload(raw_output: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    candidate: dict[str, object] | None = None
    for index, char in enumerate(raw_output):
        if char != "{":
            continue
        try:
            payload, _end_index = decoder.raw_decode(raw_output[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("ok") is True and payload.get("demoSeed") is True:
            candidate = payload

    if candidate is None:
        raise ValueError("No demo-seed JSON payload found in command output")
    return candidate


def extract_decision_payload(raw_output: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    candidate: dict[str, object] | None = None
    for index, char in enumerate(raw_output):
        if char != "{":
            continue
        try:
            payload, _end_index = decoder.raw_decode(raw_output[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        if (
            payload.get("ok") is True
            and "externalOrigins" in payload
            and payload.get("demoSeed") is not True
        ):
            candidate = payload

    if candidate is None:
        raise ValueError("No decision-smoke JSON payload found in command output")
    return candidate


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def frontend_vite_installed(root: Path | None = None) -> bool:
    target = root or frontend_dir()
    return (target / "node_modules" / "vite" / "package.json").is_file()


def ensure_frontend_dependencies(*, env: Mapping[str, str] | None = None) -> None:
    """Install frontend lockfile deps when Vite is missing. Not a CI pin."""

    root = frontend_dir()
    if frontend_vite_installed(root):
        return
    sys.stdout.write("npm ci (frontend dependencies missing)\n")
    sys.stdout.flush()
    run_foreground_command(
        [npm_command(), "ci"],
        cwd=root,
        env=env or os.environ,
        label="npm ci",
    )


def run_foreground_command(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    label: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=dict(env),
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{label} failed (exit {result.returncode})")
    return result


def run_captured_command(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    label: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed (exit {result.returncode}):\n{result.stderr}\n{result.stdout}"
        )
    return result


def open_http_url(url: str, timeout: float = 5.0) -> Any:
    hostname = urlparse(url).hostname
    if hostname in LOOPBACK_HOSTS:
        opener = build_opener(ProxyHandler({}))
        return opener.open(url, timeout=timeout)
    return urlopen(url, timeout=timeout)


def wait_for_http_ok(
    url: str, timeout_seconds: float = 60.0, poll_interval_seconds: float = 0.5
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with open_http_url(url, timeout=5) as response:
                if response.status == 200:
                    return
        except URLError as error:
            last_error = error
        except TimeoutError as error:
            last_error = error
        time.sleep(poll_interval_seconds)

    raise TimeoutError(f"Timed out waiting for HTTP 200 from {url}: {last_error}")


def terminate_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        # npm.cmd / Vite spawn children; terminate() leaves them on the port.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run_live_review_smoke(
    storage_dir: Path | None = None,
    output_dir: Path | None = None,
    host: str = DEFAULT_HOST,
    backend_port: int | None = None,
    frontend_port: int | None = None,
    skip_demo_seed: bool = False,
) -> dict[str, object]:
    target_storage_dir = (storage_dir or default_storage_dir()).resolve()
    target_output_dir = (output_dir or default_output_dir()).resolve()
    selected_backend_port = backend_port or choose_available_port(host, DEFAULT_BACKEND_PORTS)
    selected_frontend_port = frontend_port or choose_available_port(host, DEFAULT_FRONTEND_PORTS)

    backend_base_url = f"http://{host}:{selected_backend_port}"
    frontend_base_url = f"http://{host}:{selected_frontend_port}"
    frontend_origin = frontend_base_url

    backend_env = build_backend_env(
        os.environ,
        target_storage_dir,
        selected_backend_port,
        frontend_origin,
        host=host,
    )
    frontend_env = build_frontend_env(os.environ, backend_base_url)

    backend_process: subprocess.Popen[str] | None = None
    frontend_process: subprocess.Popen[str] | None = None

    try:
        backend_process = subprocess.Popen(
            [str(backend_python_executable()), "-m", "aerobim.main"],
            cwd=backend_dir(),
            env=backend_env,
            text=True,
        )
        wait_for_http_ok(f"{backend_base_url}/health")

        report = seed_smoke_report(target_storage_dir, tenant_id=SMOKE_TENANT_ID)
        ensure_frontend_dependencies(env=frontend_env)

        frontend_process = subprocess.Popen(
            [
                npm_command(),
                "run",
                "dev",
                "--",
                "--host",
                host,
                "--port",
                str(selected_frontend_port),
                "--strictPort",
            ],
            cwd=frontend_dir(),
            env=frontend_env,
            text=True,
        )
        wait_for_http_ok(frontend_base_url)

        smoke_command = [
            "node",
            str(frontend_dir() / "scripts" / "capture-review-shell-smoke.mjs"),
            "--base-url",
            frontend_base_url,
            "--output-dir",
            str(target_output_dir),
        ]
        smoke_result = run_captured_command(
            smoke_command,
            cwd=frontend_dir(),
            env=frontend_env,
            label="review-shell smoke",
        )

        decision_output_dir = target_output_dir / "decision"
        decision_command = [
            "node",
            str(frontend_dir() / "scripts" / "capture-review-decision-smoke.mjs"),
            "--base-url",
            frontend_base_url,
            "--output-dir",
            str(decision_output_dir),
        ]
        decision_result = run_captured_command(
            decision_command,
            cwd=frontend_dir(),
            env=frontend_env,
            label="review-decision smoke",
        )

        demo_payload: dict[str, object]
        if skip_demo_seed:
            demo_payload = {
                "ok": True,
                "demoSeed": False,
                "skipped": True,
                "note": "Call-path demo seed skipped by flag. Overlay fixture is a different track.",
            }
        else:
            demo_output_dir = target_output_dir / "demo"
            demo_command = [
                "node",
                str(frontend_dir() / "scripts" / "capture-demo-seed-smoke.mjs"),
                "--base-url",
                frontend_base_url,
                "--output-dir",
                str(demo_output_dir),
            ]
            demo_result = run_captured_command(
                demo_command,
                cwd=frontend_dir(),
                env=frontend_env,
                label="demo-seed smoke",
            )
            demo_payload = extract_demo_payload(demo_result.stdout)

        return {
            "stack": "vite-dev",
            "jury_cli": "python -m aerobim.tools.run_kt3_jury",
            "demo_seed_ui": "vite-dev-only",
            "backend": {
                "base_url": backend_base_url,
                "storage_dir": str(target_storage_dir),
            },
            "frontend": {
                "base_url": frontend_base_url,
                "output_dir": str(target_output_dir),
            },
            "seeded_report": build_cli_payload(report),
            "browser_smoke": extract_json_payload(smoke_result.stdout),
            "decision_smoke": extract_decision_payload(decision_result.stdout),
            "demo_seed_smoke": demo_payload,
        }
    finally:
        terminate_process(frontend_process)
        terminate_process(backend_process)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full AeroBIM live review smoke chain")
    parser.add_argument(
        "--storage-dir", type=Path, default=None, help="Override the isolated storage directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override the browser artifact output directory",
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST, help="Host used for the isolated backend/frontend stack"
    )
    parser.add_argument("--backend-port", type=int, default=None, help="Override the backend port")
    parser.add_argument(
        "--frontend-port", type=int, default=None, help="Override the frontend port"
    )
    parser.add_argument(
        "--skip-demo-seed",
        action="store_true",
        help=(
            "Skip the 15.09 call-path button (POST /v1/demo/seed-fixture). "
            "The overlay fixture from seed_smoke_report is a different track."
        ),
    )
    args = parser.parse_args()

    payload = run_live_review_smoke(
        storage_dir=args.storage_dir,
        output_dir=args.output_dir,
        host=args.host,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
        skip_demo_seed=args.skip_demo_seed,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
