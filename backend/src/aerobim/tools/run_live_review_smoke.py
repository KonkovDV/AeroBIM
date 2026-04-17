from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, build_opener, urlopen

from aerobim.tools.seed_smoke_report import build_cli_payload, repo_root, seed_smoke_report

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
) -> dict[str, str]:
    env = dict(base_env)
    env["AEROBIM_STORAGE_DIR"] = str(storage_dir)
    env["AEROBIM_PORT"] = str(port)
    env["AEROBIM_DEBUG"] = "true"
    env["AEROBIM_CORS_ORIGINS"] = frontend_origin
    return env


def build_frontend_env(base_env: Mapping[str, str], backend_base_url: str) -> dict[str, str]:
    env = dict(base_env)
    env["VITE_AEROBIM_API_BASE_URL"] = backend_base_url
    return env


def extract_json_payload(raw_output: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(raw_output):
        if char != "{":
            continue
        try:
            payload, end_index = decoder.raw_decode(raw_output[index:])
        except json.JSONDecodeError:
            continue
        if raw_output[index + end_index :].strip():
            continue
        if isinstance(payload, dict):
            return payload
    raise ValueError("No JSON payload found in smoke command output")


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def open_http_url(url: str, timeout: float = 5.0):
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
) -> dict[str, object]:
    target_storage_dir = (storage_dir or default_storage_dir()).resolve()
    target_output_dir = (output_dir or default_output_dir()).resolve()
    selected_backend_port = backend_port or choose_available_port(host, DEFAULT_BACKEND_PORTS)
    selected_frontend_port = frontend_port or choose_available_port(host, DEFAULT_FRONTEND_PORTS)

    backend_base_url = f"http://{host}:{selected_backend_port}"
    frontend_base_url = f"http://{host}:{selected_frontend_port}"
    frontend_origin = frontend_base_url

    backend_env = build_backend_env(
        os.environ, target_storage_dir, selected_backend_port, frontend_origin
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

        report = seed_smoke_report(target_storage_dir)

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
        smoke_result = subprocess.run(
            smoke_command,
            cwd=frontend_dir(),
            env=frontend_env,
            capture_output=True,
            text=True,
            check=True,
        )

        return {
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
    args = parser.parse_args()

    payload = run_live_review_smoke(
        storage_dir=args.storage_dir,
        output_dir=args.output_dir,
        host=args.host,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
