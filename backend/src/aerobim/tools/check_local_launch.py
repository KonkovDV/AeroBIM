"""Clone/laptop preflight. Not product accuracy. Checkpoint GO; customer_go false.

Mirrors a ``flutter doctor`` / ``rustup doctor`` gate: fail closed on a
broken interpreter or missing jury imports, warn on unattested CPython,
inherited closed sign-off, Store stub, and review-shell Node/ports.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, TextIO

from aerobim.tools.seed_smoke_report import repo_root

Level = Literal["fatal", "warn", "info"]

_JURY_MODULES = ("aerobim", "ifcopenshell", "ifctester", "pypdfium2")
_RASTER_MODULES = ("rapidocr", "onnxruntime")
_FIXTURE_RELATIVE = (
    "samples/ids/walls-multi-entity.ids",
    "samples/ifc/walls-multi-entity-spatial.ifc",
    "samples/demo/vertical-slice-2026-08-11/manifest.json",
)
_CLOSED_SIGNOFF = frozenset({"customer_pilot", "pilot", "production", "prod"})
_DEV_ENV = frozenset({"", "development", "dev", "test"})


@dataclass(frozen=True)
class Check:
    id: str
    ok: bool
    level: Level
    message: str


def _module_present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def check_python(
    *,
    version_info: tuple[int, int],
    executable: str,
) -> list[Check]:
    major, minor = version_info
    checks: list[Check] = []
    if (major, minor) < (3, 12):
        checks.append(
            Check(
                "python_version",
                False,
                "fatal",
                f"CPython 3.12 required; this interpreter is {major}.{minor}. "
                "Install python.org 3.12 (not Microsoft Store) and run "
                "py -3.12 -m venv .venv",
            )
        )
    elif (major, minor) != (3, 12):
        checks.append(
            Check(
                "python_version",
                False,
                "warn",
                f"CI pin is CPython 3.12; this interpreter is {major}.{minor}. "
                "Keep py -3.12 in the recipe — bare py may pick another version.",
            )
        )
    else:
        checks.append(Check("python_version", True, "info", "CPython 3.12"))
    normalized = executable.replace("/", "\\")
    if "WindowsApps" in normalized:
        checks.append(
            Check(
                "python_store_stub",
                False,
                "fatal",
                "This python.exe is the Microsoft Store stub. "
                "Install CPython 3.12 from python.org and call py -3.12.",
            )
        )
    return checks


def check_signoff(env: Mapping[str, str]) -> list[Check]:
    checks: list[Check] = []
    profile = (env.get("AEROBIM_SIGNOFF_PROFILE") or "").strip().lower()
    if profile in _CLOSED_SIGNOFF:
        checks.append(
            Check(
                "signoff_profile",
                False,
                "fatal",
                f"AEROBIM_SIGNOFF_PROFILE={profile} is a closed contour. "
                "Unset it on a first clone; the jury CLI uses the development default.",
            )
        )
    else:
        detail = profile or "unset (development default)"
        checks.append(Check("signoff_profile", True, "info", f"signoff={detail}"))
    aerobim_env = (env.get("AEROBIM_ENV") or "").strip().lower()
    if aerobim_env not in _DEV_ENV:
        checks.append(
            Check(
                "aerobim_env",
                False,
                "fatal",
                f"AEROBIM_ENV={aerobim_env} is not a development clone. "
                "Unset it, or the Shared-gate will demand clash/MEP the fixture cannot close.",
            )
        )
    return checks


def check_jury_imports() -> list[Check]:
    checks: list[Check] = []
    missing = [name for name in _JURY_MODULES if not _module_present(name)]
    if missing:
        checks.append(
            Check(
                "jury_imports",
                False,
                "fatal",
                "Missing "
                + ", ".join(missing)
                + '. From backend/: .venv\\Scripts\\python.exe -m pip install -e ".[dev,raster]"',
            )
        )
    else:
        checks.append(Check("jury_imports", True, "info", "jury imports present"))
    raster_missing = [name for name in _RASTER_MODULES if not _module_present(name)]
    if raster_missing:
        checks.append(
            Check(
                "raster_extra",
                False,
                "warn",
                "Raster extra missing ("
                + ", ".join(raster_missing)
                + "). Jury CLI (cv_sidecar off) can still run; "
                "run_demo_vertical_slice / OCR need .[raster].",
            )
        )
    else:
        checks.append(Check("raster_extra", True, "info", "raster extra present"))
    return checks


def check_fixture(root: Path) -> Check:
    missing = [rel for rel in _FIXTURE_RELATIVE if not (root / rel).is_file()]
    if missing:
        return Check(
            "fixture_pack",
            False,
            "fatal",
            "Fixture files missing: "
            + ", ".join(missing)
            + ". Clone the git tree; GitHub ZIP is not the attested path.",
        )
    return Check("fixture_pack", True, "info", "git fixture pack present")


def check_windows_hygiene(
    *,
    repo: Path,
    is_windows: bool,
    py_launcher_text: str | None,
    long_paths_enabled: bool | None,
) -> list[Check]:
    if not is_windows:
        return []
    checks: list[Check] = []
    repo_text = str(repo)
    if " " in repo_text:
        checks.append(
            Check(
                "repo_path_spaces",
                False,
                "warn",
                "Clone path contains spaces. Quote every command. Prefer C:\\AeroBIM.",
            )
        )
    if any(ord(char) > 127 for char in repo_text):
        checks.append(
            Check(
                "repo_path_ascii",
                False,
                "warn",
                "Clone path is not ASCII. Prefer a short Latin path (C:\\AeroBIM). "
                "Windows long-path + node_modules is the usual break.",
            )
        )
    if len(repo_text) > 90:
        checks.append(
            Check(
                "repo_path_length",
                False,
                "warn",
                f"Clone path is {len(repo_text)} chars. Keep it short; LongPathsEnabled may be off.",
            )
        )
    if long_paths_enabled is False:
        checks.append(
            Check(
                "windows_long_paths",
                False,
                "warn",
                "LongPathsEnabled=0. Jury CLI is fine from a short path; "
                "npm ci for the review shell can fail past MAX_PATH 260.",
            )
        )
    if py_launcher_text:
        default_line = next(
            (line for line in py_launcher_text.splitlines() if "*" in line),
            "",
        )
        if default_line and "3.12" not in default_line:
            checks.append(
                Check(
                    "py_launcher_default",
                    False,
                    "warn",
                    "Windows py launcher default is not 3.12 "
                    f"({default_line.strip()}). Always type py -3.12, not py.",
                )
            )
    return checks


def check_review_shell(
    *,
    npm_path: str | None,
    node_version: str | None,
    ports_busy: Mapping[int, bool],
) -> list[Check]:
    checks: list[Check] = []
    if npm_path is None:
        checks.append(
            Check(
                "npm",
                False,
                "fatal",
                "Node.js / npm not on PATH. Jury CLI does not need Node. "
                "Review shell needs Node 20+ (Windows: npm.cmd).",
            )
        )
    else:
        checks.append(Check("npm", True, "info", f"npm={npm_path}"))
    if node_version:
        digits = node_version.lstrip("v").split(".")
        try:
            major = int(digits[0])
        except ValueError:
            major = 0
        if major < 20:
            checks.append(
                Check(
                    "node_version",
                    False,
                    "fatal",
                    f"Node {node_version} is below 20. Review shell needs Node 20+.",
                )
            )
        else:
            checks.append(Check("node_version", True, "info", f"Node {node_version}"))
    for port, busy in ports_busy.items():
        if busy:
            checks.append(
                Check(
                    f"port_{port}",
                    False,
                    "fatal",
                    f"127.0.0.1:{port} is in use. Stop the leftover process "
                    "(API 8080, Vite 5173, never Next.js 3000).",
                )
            )
    return checks


def check_uvloop_on_windows(*, is_windows: bool, uvloop_present: bool) -> list[Check]:
    if not is_windows:
        return []
    if uvloop_present:
        return [
            Check(
                "uvloop_on_windows",
                False,
                "fatal",
                "uvloop is installed on Windows. That comes from the Linux/CI lock. "
                "Use .[dev,raster] or requirements-win-lock.txt, not requirements-lock.txt.",
            )
        ]
    return [
        Check(
            "uvloop_on_windows",
            True,
            "info",
            "uvloop absent (Linux lock not applied)",
        )
    ]


def check_git_tree(root: Path, *, git_present: bool | None = None) -> Check:
    present = (root / ".git").is_dir() if git_present is None else git_present
    if not present:
        return Check(
            "git_clone",
            False,
            "warn",
            "No .git directory. GitHub ZIP is not the attested clone. "
            "git clone https://github.com/KonkovDV/AeroBIM.git",
        )
    return Check("git_clone", True, "info", "git clone present")


def check_venv_interpreter(*, in_venv: bool) -> Check:
    if not in_venv:
        return Check(
            "venv",
            False,
            "warn",
            "This interpreter is not a venv. Use backend\\.venv\\Scripts\\python.exe "
            "or double-click run-jury.bat / .\\check-launch.bat from the clone root.",
        )
    return Check("venv", True, "info", "running inside a venv")


def check_windows_arch(*, is_windows: bool, machine: str) -> list[Check]:
    if not is_windows:
        return []
    normalized = machine.lower().replace("-", "")
    if normalized in {"amd64", "x86_64", "x64"}:
        return [Check("windows_arch", True, "info", f"arch={machine}")]
    return [
        Check(
            "windows_arch",
            False,
            "warn",
            f"CPU is {machine}. requirements-win-lock.txt is x86_64. "
            "Prefer the pip extra recipe on x64 CPython; ARM64 wheels are unattested.",
        )
    ]


def check_ifcopenshell_import(*, import_ok: bool | None = None, error: str = "") -> Check:
    if import_ok is None:
        try:
            importlib.import_module("ifcopenshell")
            import_ok = True
            error = ""
        except Exception as exc:
            import_ok = False
            error = f"{type(exc).__name__}: {exc}"
    if not import_ok:
        return Check(
            "ifcopenshell_import",
            False,
            "fatal",
            "IfcOpenShell failed to import"
            + (f" ({error})" if error else "")
            + ". On Windows install the Microsoft VC++ 2015-2022 x64 redistributable, "
            "then retry .\\run-jury.bat.",
        )
    return Check("ifcopenshell_import", True, "info", "IfcOpenShell imports")


def check_loopback_for_jury(ports_busy: Mapping[int, bool]) -> list[Check]:
    if ports_busy.get(8080):
        return [
            Check(
                "port_8080",
                False,
                "warn",
                "127.0.0.1:8080 is in use (often leftover Docker). "
                "Jury CLI does not need it. .\\start.bat will fail until it is free.",
            )
        ]
    return []


def collect_checks(
    *,
    env: Mapping[str, str],
    version_info: tuple[int, int],
    executable: str,
    root: Path,
    is_windows: bool,
    review_shell: bool = False,
    py_launcher_text: str | None = None,
    long_paths_enabled: bool | None = None,
    npm_path: str | None = None,
    node_version: str | None = None,
    ports_busy: Mapping[int, bool] | None = None,
    uvloop_present: bool | None = None,
    git_present: bool | None = None,
    in_venv: bool = True,
    machine: str = "AMD64",
    ifcopenshell_ok: bool | None = True,
    ifcopenshell_error: str = "",
) -> list[Check]:
    checks: list[Check] = []
    checks.extend(check_python(version_info=version_info, executable=executable))
    checks.extend(check_signoff(env))
    checks.extend(check_jury_imports())
    checks.append(check_ifcopenshell_import(import_ok=ifcopenshell_ok, error=ifcopenshell_error))
    checks.append(check_fixture(root))
    checks.append(check_git_tree(root, git_present=git_present))
    checks.append(check_venv_interpreter(in_venv=in_venv))
    checks.extend(check_windows_arch(is_windows=is_windows, machine=machine))
    checks.extend(
        check_windows_hygiene(
            repo=root,
            is_windows=is_windows,
            py_launcher_text=py_launcher_text,
            long_paths_enabled=long_paths_enabled,
        )
    )
    checks.extend(
        check_uvloop_on_windows(
            is_windows=is_windows,
            uvloop_present=_module_present("uvloop") if uvloop_present is None else uvloop_present,
        )
    )
    busy = ports_busy or {}
    if review_shell:
        checks.extend(
            check_review_shell(
                npm_path=npm_path,
                node_version=node_version,
                ports_busy=busy,
            )
        )
    else:
        checks.extend(check_loopback_for_jury(busy))
    return checks


def worst_exit(checks: Sequence[Check]) -> int:
    if any(not item.ok and item.level == "fatal" for item in checks):
        return 2
    if any(not item.ok and item.level == "warn" for item in checks):
        return 1
    return 0


def _py_launcher_list() -> str | None:
    if os.name != "nt":
        return None
    try:
        completed = subprocess.run(
            ["py", "-0p"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, TimeoutError):
        return None
    text = (completed.stdout or "") + (completed.stderr or "")
    return text or None


def _long_paths_enabled() -> bool | None:
    # sys.platform, not os.name: mypy on Linux treats the win32 branch as unreachable.
    if sys.platform != "win32":
        return None
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
    except OSError:
        return None
    return bool(value)


def _node_version() -> str | None:
    try:
        completed = subprocess.run(
            ["node", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, TimeoutError):
        return None
    text = (completed.stdout or "").strip()
    return text or None


def _ports_busy(ports: tuple[int, ...] = (8080, 5173)) -> dict[int, bool]:
    busy: dict[int, bool] = {}
    for port in ports:
        sock = socket.socket()
        sock.settimeout(0.25)
        try:
            busy[port] = sock.connect_ex(("127.0.0.1", port)) == 0
        finally:
            sock.close()
    return busy


def live_checks(*, review_shell: bool = False) -> list[Check]:
    ports = (8080, 5173) if review_shell else (8080,)
    return collect_checks(
        env=os.environ,
        version_info=sys.version_info[:2],
        executable=sys.executable,
        root=repo_root(),
        is_windows=os.name == "nt",
        review_shell=review_shell,
        py_launcher_text=_py_launcher_list(),
        long_paths_enabled=_long_paths_enabled(),
        npm_path=shutil.which("npm.cmd") or shutil.which("npm"),
        node_version=_node_version() if review_shell else None,
        ports_busy=_ports_busy(ports),
        git_present=None,
        in_venv=sys.prefix != sys.base_prefix,
        machine=platform.machine(),
        ifcopenshell_ok=None,
    )


def emit_preflight(
    *,
    stream: TextIO,
    review_shell: bool = False,
    checks: Sequence[Check] | None = None,
) -> int:
    items = list(checks if checks is not None else live_checks(review_shell=review_shell))
    for item in items:
        if item.ok:
            continue
        tag = item.level.upper()
        stream.write(f"check_local_launch {tag} {item.id}: {item.message}\n")
    stream.flush()
    return worst_exit(items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--review-shell",
        action="store_true",
        help="Also check Node 20+, npm, and ports 8080/5173.",
    )
    args = parser.parse_args(argv)
    checks = live_checks(review_shell=args.review_shell)
    payload = {
        "checkpoint": "GO",
        "customer_go": False,
        "exit": worst_exit(checks),
        "checks": [asdict(item) for item in checks],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        emit_preflight(stream=sys.stderr, checks=checks)
        print(
            json.dumps(
                {
                    "ok": payload["exit"] != 2,
                    "exit": payload["exit"],
                    "fatal": [item.id for item in checks if not item.ok and item.level == "fatal"],
                    "warn": [item.id for item in checks if not item.ok and item.level == "warn"],
                    "customer_go": False,
                },
                ensure_ascii=False,
            )
        )
    return payload["exit"] if payload["exit"] == 2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
