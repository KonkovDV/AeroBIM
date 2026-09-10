"""IT-mentor laptop track: empty storage + Vite-dev review shell.

Jury track remains ``python -m aerobim.tools.run_kt3_jury``.
Does not seed the overlay fixture. Click «Загрузить демонстрационный комплект».
Not a customer pack. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO
from aerobim.tools.run_live_review_smoke import (
    backend_dir,
    backend_python_executable,
    build_backend_env,
    build_frontend_env,
    choose_available_port,
    ensure_frontend_dependencies,
    frontend_dir,
    npm_command,
    terminate_process,
    wait_for_http_ok,
)
from aerobim.tools.seed_smoke_report import repo_root

CLAIM_BOUNDARY = (
    "IT-mentor Vite-dev stand. Dedicated .local storage (reused, not wiped), "
    "then POST /v1/demo/seed-fixture. "
    "Not jury CLI. Not a customer pack. Not product accuracy. "
    "Checkpoint GO; customer_go false."
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORTS = (8080, 8081)
DEFAULT_FRONTEND_PORTS = (5173, 3000)


def default_storage_dir() -> Path:
    return repo_root() / ".local" / "mentor-demo-stand"


def print_stand_card(*, frontend_url: str, backend_url: str, storage: Path) -> None:
    sys.stdout.write(
        "\n".join(
            [
                f"checkpoint={CHECKPOINT} customer_go={CUSTOMER_GO}",
                CLAIM_BOUNDARY,
                f"frontend {frontend_url}",
                f"backend  {backend_url}",
                f"storage  {storage}",
                "Click: Загрузить демонстрационный комплект",
                "Do not say: пакет заказчика обработан, SLA, CDE-ready, native RVT.",
                "Ctrl+C stops both processes.",
                "",
            ]
        )
    )
    sys.stdout.flush()


def run_it_mentor_stand(
    storage_dir: Path | None = None,
    host: str = DEFAULT_HOST,
    backend_port: int | None = None,
    frontend_port: int | None = None,
) -> None:
    target_storage = (storage_dir or default_storage_dir()).resolve()
    target_storage.mkdir(parents=True, exist_ok=True)
    selected_backend = backend_port or choose_available_port(host, DEFAULT_BACKEND_PORTS)
    selected_frontend = frontend_port or choose_available_port(host, DEFAULT_FRONTEND_PORTS)
    backend_url = f"http://{host}:{selected_backend}"
    frontend_url = f"http://{host}:{selected_frontend}"

    backend_env = build_backend_env(
        os.environ, target_storage, selected_backend, frontend_url, host=host
    )
    frontend_env = build_frontend_env(os.environ, backend_url)

    backend_process: subprocess.Popen[str] | None = None
    frontend_process: subprocess.Popen[str] | None = None
    try:
        backend_process = subprocess.Popen(
            [str(backend_python_executable()), "-m", "aerobim.main"],
            cwd=backend_dir(),
            env=backend_env,
            text=True,
        )
        wait_for_http_ok(f"{backend_url}/health")
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
                str(selected_frontend),
                "--strictPort",
            ],
            cwd=frontend_dir(),
            env=frontend_env,
            text=True,
        )
        wait_for_http_ok(frontend_url)
        print_stand_card(
            frontend_url=frontend_url,
            backend_url=backend_url,
            storage=target_storage,
        )
        while True:
            if backend_process.poll() is not None:
                raise RuntimeError("backend process exited")
            if frontend_process.poll() is not None:
                raise RuntimeError("frontend process exited")
            time.sleep(0.5)
    except KeyboardInterrupt:
        sys.stdout.write("stopping mentor stand\n")
        sys.stdout.flush()
    finally:
        terminate_process(frontend_process)
        terminate_process(backend_process)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "One-command IT-mentor review shell: API + Vite. "
            "Dedicated .local storage, no overlay seed. Not the jury CLI."
        )
    )
    parser.add_argument("--storage-dir", type=Path, default=None)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--backend-port", type=int, default=None)
    parser.add_argument("--frontend-port", type=int, default=None)
    args = parser.parse_args()
    run_it_mentor_stand(
        storage_dir=args.storage_dir,
        host=args.host,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
    )


if __name__ == "__main__":
    main()
