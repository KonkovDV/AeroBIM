"""Offline deployment bundle for closed contours (P-002, image-based).

Honest scope: the bundle carries the production Docker image (saved tar built
from hash-locked wheels + digest-pinned base), the dependency locks, Dockerfile
and a sha256 manifest. `smoke` proves offline INSTALL (docker load from tar,
after removing the tag) + offline RUNTIME (`--network none`, in-container probes).
Bare-metal pip wheelhouse is OUT_OF_SCOPE for И1.

Subcommands:
  build           -> artifacts/offline-bundle/ (image tar + locks + SBOM-lite + install scripts)
  verify          -> recompute sha256 of every bundle file against the manifest
  smoke           -> docker rmi tag; docker load -i tar; run --network none; API checks
  closed-contour  -> verify (+ optional --smoke) + operator checklist for И1 Docker track
  wheelhouse      -> OUT_OF_SCOPE honesty artifact (bare-metal pip; not required when Docker works)
  sbom            -> SPDX-lite JSON from requirements-lock.txt (no network)
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3].parent
_BACKEND = _REPO_ROOT / "backend"
_BUNDLE_DIR = _REPO_ROOT / "artifacts" / "offline-bundle"
_IMAGE_TAG = "aerobim-backend:offline-bundle"
_IMAGE_TAR = "aerobim-backend-image.tar"
_MANIFEST = "BUNDLE_MANIFEST.json"
_SBOM = "sbom-spdx-lite.json"
_INSTALL = "INSTALL_OFFLINE.md"
_MIRROR = "MIRROR_CHECKLIST.md"
_INSTALL_SH = "install_offline.sh"
_INSTALL_PS1 = "install_offline.ps1"
_WHEELHOUSE_ARTIFACT = "wheelhouse-OUT_OF_SCOPE.json"
_DEMO_TOKEN = "offline-bundle-token"
_CONTAINER_NAME = "aerobim-offline"
_BUNDLE_FILES = (
    _IMAGE_TAR,
    "requirements-lock.txt",
    "requirements-dev-lock.txt",
    "Dockerfile",
)
_DOC_FILES = (_INSTALL, _SBOM, _MIRROR, _INSTALL_SH, _INSTALL_PS1, _WHEELHOUSE_ARTIFACT)

_PIN_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\\\s#]+)")
_HASH_RE = re.compile(r"--hash=sha256:([0-9a-fA-F]+)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_lock_packages(lock_text: str) -> list[dict[str, object]]:
    """Extract name/version/hashes from a pip-tools / uv hash lock (RT-019 SBOM-lite)."""

    packages: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for raw in lock_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pin = _PIN_RE.match(line.rstrip("\\").strip())
        if pin:
            if current is not None:
                packages.append(current)
            current = {
                "name": pin.group(1).lower(),
                "versionInfo": pin.group(2),
                "checksums": [],
            }
        if current is None:
            continue
        for digest in _HASH_RE.findall(line):
            hashes = current["checksums"]
            assert isinstance(hashes, list)
            hashes.append(f"SHA256:{digest}")
    if current is not None:
        packages.append(current)
    return packages


def build_spdx_lite(*, lock_path: Path, image_id: str) -> dict[str, object]:
    packages = parse_lock_packages(lock_path.read_text(encoding="utf-8"))
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "aerobim-offline-bundle-sbom-lite",
        "documentNamespace": f"https://aerobim.local/spdx/{image_id[:19]}",
        "creationInfo": {
            "created": datetime.now(tz=UTC).isoformat(),
            "creators": ["Tool: aerobim.tools.offline_bundle"],
            "comment": (
                "SPDX-lite generated from requirements-lock.txt only. "
                "Not a full CycloneDX graph; no GitVerse mirror claim."
            ),
        },
        "packages": [
            {
                "SPDXID": f"SPDXRef-Package-{pkg['name']}",
                "name": pkg["name"],
                "versionInfo": pkg["versionInfo"],
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": h.split(":", 1)[1]}
                    for h in (pkg["checksums"] if isinstance(pkg["checksums"], list) else [])
                    if isinstance(h, str) and h.startswith("SHA256:")
                ],
            }
            for pkg in packages
        ],
        "claim_level": "lockfile_sbom_lite",
        "package_count": len(packages),
    }


def _container_probe_command() -> str:
    """In-container probes: health, auth gate, capabilities, egress block (token from env)."""

    body = """import os, urllib.request, urllib.error, socket
tok = os.environ.get("AEROBIM_API_BEARER_TOKEN", "")
if not tok:
    raise SystemExit("missing AEROBIM_API_BEARER_TOKEN")
h = urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=5)
assert h.status == 200
try:
    urllib.request.urlopen("http://127.0.0.1:8080/v1/system/capabilities", timeout=3)
except urllib.error.HTTPError as exc:
    assert exc.code == 401
else:
    raise SystemExit("unauthenticated capabilities must return 401")
req = urllib.request.Request(
    "http://127.0.0.1:8080/v1/system/capabilities",
    headers={"Authorization": "Bearer " + tok},
)
c = urllib.request.urlopen(req, timeout=5)
assert c.status == 200
try:
    socket.create_connection(("1.1.1.1", 80), 2).close()
except OSError:
    pass
else:
    raise SystemExit("egress not blocked under --network none")
print("offline bundle probes: health+auth+egress OK")
"""
    encoded = base64.b64encode(body.encode("utf-8")).decode("ascii")
    return f"import base64; exec(base64.b64decode({encoded!r}))"


def _container_probe_script(*, token: str = "") -> str:
    """Backward-compatible alias; token is read from container env at runtime."""

    _ = token
    return _container_probe_command()


def write_wheelhouse_artifact(bundle_dir: Path) -> None:
    payload = {
        "artifact_type": "aerobim_offline_wheelhouse",
        "schema_version": "1.1.0",
        "status": "OUT_OF_SCOPE",
        "exit_code": 2,
        "claim_level": "not_required",
        "scope_honesty": (
            "Bare-metal pip wheelhouse offline install is OUT_OF_SCOPE for И1. "
            "Docker image-track bundle (build|verify|smoke|closed-contour) is the "
            "verified closed-contour path when the host provides Docker."
        ),
        "verified_path": "docker image bundle (offline_bundle build|verify|smoke|closed-contour)",
        "out_of_scope_path": "pip wheelhouse + venv install without Docker",
        "i1_status": "CLOSED_DOCKER_TRACK",
    }
    (bundle_dir / _WHEELHOUSE_ARTIFACT).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    legacy = bundle_dir / "wheelhouse-DEFERRED.json"
    legacy.write_text(
        json.dumps({**payload, "status": "DEFERRED", "legacy_alias": True}, indent=2) + "\n",
        encoding="utf-8",
    )


def write_install_scripts(bundle_dir: Path) -> None:
    probe_cmd = _container_probe_command()
    probe_shell = json.dumps(probe_cmd)
    (bundle_dir / _INSTALL_SH).write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
                'IMAGE_TAR="${SCRIPT_DIR}/aerobim-backend-image.tar"',
                'IMAGE_TAG="aerobim-backend:offline-bundle"',
                'TOKEN="${AEROBIM_API_BEARER_TOKEN:-}"',
                f'CONTAINER="{_CONTAINER_NAME}"',
                'ALLOW_DEMO="${AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN:-}"',
                "",
                "if ! command -v docker >/dev/null 2>&1; then",
                '  echo "Docker is required for the closed-contour install track." >&2',
                "  exit 1",
                "fi",
                'if [ -z "${TOKEN}" ]; then',
                '  echo "Set AEROBIM_API_BEARER_TOKEN before install (no default in production)." >&2',
                "  exit 1",
                "fi",
                'if [ "${TOKEN}" = "' + _DEMO_TOKEN + '" ] && [ "${ALLOW_DEMO}" != "1" ]; then',
                '  echo "Refusing demo token; set AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN=1 for lab only." >&2',
                "  exit 1",
                "fi",
                "",
                'echo "Loading image from tar (air-gap install)..."',
                'docker load -i "${IMAGE_TAR}"',
                "",
                'docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true',
                'echo "Starting backend (--network none; API via docker exec only)..."',
                "docker run -d --rm \\",
                '  --name "${CONTAINER}" \\',
                "  --network none \\",
                '  -e "AEROBIM_API_BEARER_TOKEN=${TOKEN}" \\',
                '  -e "AEROBIM_ENV=development" \\',
                '  "${IMAGE_TAG}"',
                "",
                "sleep 8",
                f'docker exec "${{CONTAINER}}" python -c {probe_shell}',
                'echo "Install OK (full closed-contour probe passed)."',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_dir / _INSTALL_PS1).write_text(
        "\n".join(
            [
                "# AeroBIM offline closed-contour install (Docker image-track)",
                "$ErrorActionPreference = 'Stop'",
                "$BundleDir = Split-Path -Parent $MyInvocation.MyCommand.Path",
                '$ImageTar = Join-Path $BundleDir "aerobim-backend-image.tar"',
                '$ImageTag = "aerobim-backend:offline-bundle"',
                f'$Container = "{_CONTAINER_NAME}"',
                "if (-not $env:AEROBIM_API_BEARER_TOKEN) {",
                '  throw "Set AEROBIM_API_BEARER_TOKEN before install (no default in production)."',
                "}",
                'if ($env:AEROBIM_API_BEARER_TOKEN -eq "'
                + _DEMO_TOKEN
                + '" -and $env:AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN -ne "1") {',
                '  throw "Refusing demo token; set AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN=1 for lab only."',
                "}",
                "",
                "if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {",
                '  throw "Docker is required for the closed-contour install track."',
                "}",
                "",
                'Write-Host "Loading image from tar (air-gap install)..."',
                "docker load -i $ImageTar",
                "",
                "docker rm -f $Container 2>$null | Out-Null",
                'Write-Host "Starting backend (--network none; API via docker exec only)..."',
                "docker run -d --rm `",
                "  --name $Container `",
                "  --network none `",
                '  -e "AEROBIM_API_BEARER_TOKEN=$($env:AEROBIM_API_BEARER_TOKEN)" `',
                '  -e "AEROBIM_ENV=development" `',
                "  $ImageTag",
                "",
                "Start-Sleep -Seconds 8",
                f"docker exec $Container python -c {probe_shell}",
                'Write-Host "Install OK (full closed-contour probe passed)."',
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_install_docs(bundle_dir: Path) -> None:
    (bundle_dir / _INSTALL).write_text(
        "\n".join(
            [
                "# AeroBIM offline install (Docker image-track)",
                "",
                "**Claim:** docker load + `--network none` runtime. Host must provide Docker.",
                "**И1 closed-contour:** Docker image-track is the verified install path.",
                "**Out of scope:** bare-metal pip wheelhouse (see wheelhouse-OUT_OF_SCOPE.json).",
                "",
                "## Quick install",
                "",
                "- Linux/macOS: `./install_offline.sh`",
                "- Windows: `powershell -File .\\install_offline.ps1`",
                "",
                "## Steps (air-gapped host with Docker)",
                "",
                "1. Copy this directory to the host (USB / internal share).",
                "2. `docker load -i aerobim-backend-image.tar`",
                "3. `docker run -d --rm --name aerobim-offline --network none \\`",
                "   `-e AEROBIM_API_BEARER_TOKEN=<secret> -e AEROBIM_ENV=development \\`",
                "   `aerobim-backend:offline-bundle`",
                "4. Full probe (install scripts run this automatically):",
                "   `docker exec aerobim-offline python -c '<closed-contour probe>'`",
                "   Checks health, 401 without auth, capabilities with bearer, egress block.",
                "   (Host `-p` port mapping is **unreliable** with `--network none` on some engines.)",
                "5. Recompute sha256 of files listed in BUNDLE_MANIFEST.json (or run verify).",
                "",
                "## SBOM",
                "",
                "`sbom-spdx-lite.json` lists locked runtime pins from requirements-lock.txt.",
                "",
                "## RF supply note",
                "",
                "If Docker Hub / PyPI / GitHub are unreachable, build the bundle on a",
                "connected builder and transfer the tar. See MIRROR_CHECKLIST.md.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (bundle_dir / _MIRROR).write_text(
        "\n".join(
            [
                "# Mirror checklist (RT-019) — operator, not product claim",
                "",
                "| Source | Risk in RF contour | Mitigation |",
                "|---|---|---|",
                "| Docker Hub | IP blocks / rate limits | Transfer "
                "`aerobim-backend-image.tar`; optional GitVerse/Docker mirror |",
                "| PyPI | Outages | Hash locks inside image; do not pip-install on air-gap host |",
                "| GitHub | Clone/push timeouts | Ship release pack + "
                "GitVerse mirror of this repo (operator) |",
                "",
                "GitVerse (from 2026-06-16 public claim): PyPI/Go/Crates/Docker Hub mirrors —",
                "verify current operator docs before relying; AeroBIM does "
                "**not** claim a live mirror.",
                "",
                "**Owner decision (2026-08-08):** И1 closed-contour = Docker image-track.",
                "Bare-metal wheelhouse is OUT_OF_SCOPE while Docker offline smoke passes.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build_manifest(bundle_dir: Path, *, image_id: str) -> dict[str, object]:
    files = {}
    for name in (*_BUNDLE_FILES, *_DOC_FILES):
        path = bundle_dir / name
        if not path.is_file():
            continue
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return {
        "artifact_type": "aerobim_offline_bundle",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "image_tag": _IMAGE_TAG,
        "image_id": image_id,
        "claim_level": "image_bundle_only",
        "scope_honesty": (
            "image-based closed-contour bundle (И1 Docker track): offline install = docker load, "
            "offline runtime proven with --network none; target host must "
            "provide Docker; bare-metal wheelhouse OUT_OF_SCOPE; "
            "sbom-spdx-lite = lockfile pins only (not full graph / not GitVerse)"
        ),
        "files": files,
    }


def verify_bundle_source_sync(bundle_dir: Path) -> list[str]:
    """Detect bundle lock/Dockerfile drift from live backend source (builder-side)."""

    problems: list[str] = []
    for name in ("requirements-lock.txt", "requirements-dev-lock.txt", "Dockerfile"):
        bundle_path = bundle_dir / name
        backend_path = _BACKEND / name
        if not bundle_path.is_file() or not backend_path.is_file():
            continue
        if sha256_file(bundle_path) != sha256_file(backend_path):
            problems.append(f"bundle/backend drift: {name}")
    return problems


def verify_manifest(bundle_dir: Path) -> list[str]:
    """Return a list of mismatches (empty == verified)."""
    manifest = json.loads((bundle_dir / _MANIFEST).read_text(encoding="utf-8"))
    problems: list[str] = []
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["manifest has no files map"]
    for name, meta in files.items():
        path = bundle_dir / name
        if not path.is_file():
            problems.append(f"missing: {name}")
            continue
        if sha256_file(path) != meta.get("sha256"):
            problems.append(f"sha256 mismatch: {name}")
    return problems


def _docker(*args: str, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=timeout, check=False
    )


def cmd_sbom(*, image_id: str = "sha256:local") -> int:
    """Write SPDX-lite from the backend runtime lock (no network)."""

    _BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    lock = _BACKEND / "requirements-lock.txt"
    if not lock.is_file():
        print(f"missing lock: {lock}")
        return 1
    payload = build_spdx_lite(lock_path=lock, image_id=image_id)
    out = _BUNDLE_DIR / _SBOM
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"sbom-lite written: {out} packages={payload['package_count']}")
    return 0


def cmd_build() -> int:
    _BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    build = _docker("build", "-t", _IMAGE_TAG, str(_BACKEND))
    if build.returncode != 0:
        print(build.stderr[-800:])
        return 1
    image_id = _docker("images", "--no-trunc", "-q", _IMAGE_TAG).stdout.strip()
    save = _docker("save", "-o", str(_BUNDLE_DIR / _IMAGE_TAR), _IMAGE_TAG)
    if save.returncode != 0:
        print(save.stderr[-800:])
        return 1
    for name in ("requirements-lock.txt", "requirements-dev-lock.txt", "Dockerfile"):
        (_BUNDLE_DIR / name).write_bytes((_BACKEND / name).read_bytes())
    write_install_docs(_BUNDLE_DIR)
    write_install_scripts(_BUNDLE_DIR)
    write_wheelhouse_artifact(_BUNDLE_DIR)
    if cmd_sbom(image_id=image_id or "sha256:unknown") != 0:
        return 1
    manifest = build_manifest(_BUNDLE_DIR, image_id=image_id)
    (_BUNDLE_DIR / _MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"bundle built: {_BUNDLE_DIR} image_id={image_id[:19]}...")
    return 0


def cmd_verify() -> int:
    problems = verify_manifest(_BUNDLE_DIR) + verify_bundle_source_sync(_BUNDLE_DIR)
    if problems:
        print("BUNDLE VERIFY FAILED:\n" + "\n".join(problems))
        return 1
    print("bundle verified: all sha256 match; no bundle/backend drift")
    return 0


def cmd_smoke() -> int:
    """Offline install + runtime proof: rmi tag -> load from tar -> run --network none."""
    container = "aerobim-offline-bundle-smoke"
    token = _DEMO_TOKEN
    _docker("rm", "-f", container)
    _docker("rmi", "-f", _IMAGE_TAG)
    load = _docker("load", "-i", str(_BUNDLE_DIR / _IMAGE_TAR))
    if load.returncode != 0:
        print(load.stderr[-800:])
        return 1
    run = _docker(
        "run",
        "-d",
        "--name",
        container,
        "--network",
        "none",
        "-e",
        f"AEROBIM_API_BEARER_TOKEN={token}",
        "-e",
        "AEROBIM_OFFLINE_ALLOW_DEMO_TOKEN=1",
        "-e",
        "AEROBIM_ENV=development",
        _IMAGE_TAG,
    )
    if run.returncode != 0:
        print(run.stderr[-800:])
        return 1
    try:
        time.sleep(8)
        status = _docker("ps", "--filter", f"name={container}", "--format", "{{.Status}}")
        if "Up" not in status.stdout:
            logs = _docker("logs", container)
            print("container not up:", status.stdout, logs.stdout[-500:], logs.stderr[-500:])
            return 1
        probe = _docker(
            "exec",
            container,
            "python",
            "-c",
            _container_probe_command(),
        )
        print(probe.stdout.strip() or probe.stderr[-400:])
        return 0 if probe.returncode == 0 else 1
    finally:
        _docker("rm", "-f", container)


def cmd_closed_contour(*, run_smoke: bool = False) -> int:
    """И1 operator gate: manifest verify + optional docker smoke."""

    problems = verify_manifest(_BUNDLE_DIR) + verify_bundle_source_sync(_BUNDLE_DIR)
    if problems:
        print("CLOSED-CONTOUR VERIFY FAILED:\n" + "\n".join(problems))
        return 1
    print("closed-contour: manifest sha256 OK; no bundle/backend drift")
    if run_smoke:
        smoke_rc = cmd_smoke()
        if smoke_rc != 0:
            print("closed-contour: smoke FAILED")
            return smoke_rc
        print("closed-contour: smoke OK (docker load + --network none)")
    else:
        print("closed-contour: run with --smoke to prove docker load + --network none")
    print(f"bundle dir: {_BUNDLE_DIR}")
    print("operator docs: docs/offline-deployment-2026.md")
    return 0


def cmd_wheelhouse() -> int:
    """Bare-metal wheelhouse — OUT_OF_SCOPE when Docker closed-contour is verified."""

    _BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    write_wheelhouse_artifact(_BUNDLE_DIR)
    artifact_path = _BUNDLE_DIR / _WHEELHOUSE_ARTIFACT
    print("OUT_OF_SCOPE: bare-metal wheelhouse not required — use Docker image-track.")
    print(f"honesty artifact: {artifact_path}")
    return 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline deployment bundle (image-based)")
    parser.add_argument(
        "command",
        choices=("build", "verify", "smoke", "closed-contour", "wheelhouse", "sbom"),
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="With closed-contour: also run docker load + --network none smoke",
    )
    args = parser.parse_args()
    handlers: dict[str, Callable[[], int]] = {
        "build": cmd_build,
        "verify": cmd_verify,
        "smoke": cmd_smoke,
        "closed-contour": lambda: cmd_closed_contour(run_smoke=args.smoke),
        "wheelhouse": cmd_wheelhouse,
        "sbom": cmd_sbom,
    }
    sys.exit(handlers[args.command]())


if __name__ == "__main__":
    main()
