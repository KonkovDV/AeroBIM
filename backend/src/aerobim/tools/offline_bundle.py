"""Offline deployment bundle for closed contours (P-002, image-based).

Honest scope: the bundle carries the production Docker image (saved tar built
from hash-locked wheels + digest-pinned base), the dependency locks, Dockerfile
and a sha256 manifest. `smoke` proves offline INSTALL (docker load from tar,
after removing the tag) + offline RUNTIME (--network none API checks). The
target host still needs Docker itself; bare-metal wheelhouse install remains
NOT VERIFIED and is not claimed.

Subcommands:
  build   -> artifacts/offline-bundle/ (image tar + locks + BUNDLE_MANIFEST.json)
  verify  -> recompute sha256 of every bundle file against the manifest
  smoke   -> docker rmi tag; docker load -i tar; run --network none; API checks
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3].parent
_BACKEND = _REPO_ROOT / "backend"
_BUNDLE_DIR = _REPO_ROOT / "artifacts" / "offline-bundle"
_IMAGE_TAG = "aerobim-backend:offline-bundle"
_IMAGE_TAR = "aerobim-backend-image.tar"
_MANIFEST = "BUNDLE_MANIFEST.json"
_BUNDLE_FILES = (
    _IMAGE_TAR,
    "requirements-lock.txt",
    "requirements-dev-lock.txt",
    "Dockerfile",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(bundle_dir: Path, *, image_id: str) -> dict[str, object]:
    files = {}
    for name in _BUNDLE_FILES:
        path = bundle_dir / name
        files[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return {
        "artifact_type": "aerobim_offline_bundle",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "image_tag": _IMAGE_TAG,
        "image_id": image_id,
        "claim_level": "image_bundle_only",
        "scope_honesty": (
            "image-based closed-contour bundle: offline install = docker load, "
            "offline runtime proven with --network none; target host must "
            "provide Docker; bare-metal wheelhouse install NOT VERIFIED"
        ),
        "files": files,
    }


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
    manifest = build_manifest(_BUNDLE_DIR, image_id=image_id)
    (_BUNDLE_DIR / _MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"bundle built: {_BUNDLE_DIR} image_id={image_id[:19]}...")
    return 0


def cmd_verify() -> int:
    problems = verify_manifest(_BUNDLE_DIR)
    if problems:
        print("BUNDLE VERIFY FAILED:\n" + "\n".join(problems))
        return 1
    print("bundle verified: all sha256 match")
    return 0


def cmd_smoke() -> int:
    """Offline install + runtime proof: rmi tag -> load from tar -> run --network none."""
    container = "aerobim-offline-bundle-smoke"
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
        "AEROBIM_API_BEARER_TOKEN=offline-bundle-token",
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
            (
                "import urllib.request,urllib.error;"
                "h=urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=5);"
                "assert h.status==200;"
                "r=urllib.request.Request('http://127.0.0.1:8080/v1/system/capabilities',"
                "headers={'Authorization':'Bearer offline-bundle-token'});"
                "c=urllib.request.urlopen(r,timeout=5);assert c.status==200;"
                "print('offline bundle smoke: health+capabilities OK')"
            ),
        )
        print(probe.stdout.strip() or probe.stderr[-400:])
        return 0 if probe.returncode == 0 else 1
    finally:
        _docker("rm", "-f", container)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline deployment bundle (image-based)")
    parser.add_argument("command", choices=("build", "verify", "smoke"))
    args = parser.parse_args()
    sys.exit({"build": cmd_build, "verify": cmd_verify, "smoke": cmd_smoke}[args.command]())


if __name__ == "__main__":
    main()
