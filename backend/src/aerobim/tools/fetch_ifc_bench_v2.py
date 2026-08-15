"""Stage IFC-Bench v2 into gitignored ``.local/ifc-bench-v2``.

Prefers a local checkout (``--from-dir``). Hub download is best-effort and
tries huggingface.co then hf-mirror.com. Skips GPLv3 project directories
listed in IMPORT_PINS.json unless ``--samolet-demo-copyleft --include-gplv3``
(local gitignored ``.local/`` only; refused in CI). Does not add
huggingface_hub as a product dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from aerobim.domain.copyleft_lane import (
    GPLV3_IFC_BENCH_PROJECTS,
    local_samolet_demo_copyleft_inputs_permitted,
)
from aerobim.tools.benchmark_project_package import repo_root

DEFAULT_HUB = "https://huggingface.co"
MIRROR_HUB = "https://hf-mirror.com"
HUB_API_PATH = "/api/datasets/sylvainHellin/ifc-bench/tree/main"
HUB_RESOLVE_PATH = "/datasets/sylvainHellin/ifc-bench/resolve/main"
PRIORITY_PREFIXES = (
    "questions/",
    "projects/duplex/",
    "projects/dental_clinic/",
    "projects/digital_hub/",
    "projects/west_riverside_hospital/",
    "projects/wbdg_office/",
    "projects/sixty5/",
    "README.md",
    "LICENSE",
)
def _local_candidates() -> list[Path]:
    """Repo-relative and sibling checkouts. No machine-absolute paths."""
    candidates: list[Path] = []
    env = os.environ.get("AEROBIM_IFC_BENCH_V2")
    if env:
        candidates.append(Path(env))
    root = repo_root()
    candidates.append(root / ".local" / "ifc-bench-v2")
    candidates.append(root.parent / "AeroBIM-private" / ".local" / "ifc-bench-v2")
    return candidates


def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def _load_gpl_excludes(repo: Path) -> set[str]:
    pins = repo / "samples" / "benchmarks" / "ifc-bench-v2" / "IMPORT_PINS.json"
    if not pins.is_file():
        return set(GPLV3_IFC_BENCH_PROJECTS)
    payload = json.loads(pins.read_text(encoding="utf-8"))
    names = payload.get("gplv3_models_exclude_from_mit_tree") or list(GPLV3_IFC_BENCH_PROJECTS)
    return {str(name) for name in names}


def _is_gpl_path(rel: str, excludes: set[str]) -> bool:
    parts = Path(rel.replace("\\", "/")).parts
    return any(part in excludes for part in parts)


def _hubs() -> list[str]:
    env = (os.environ.get("HF_ENDPOINT") or "").strip().rstrip("/")
    hubs = [env] if env else []
    for candidate in (DEFAULT_HUB, MIRROR_HUB):
        if candidate not in hubs:
            hubs.append(candidate)
    return hubs


def list_hub_files() -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for hub in _hubs():
        url = f"{hub}{HUB_API_PATH}?recursive=1"
        req = urllib.request.Request(url, headers={"User-Agent": "AeroBIM-fetch/1.0"})
        try:
            with urllib.request.urlopen(req, context=_ssl_context(), timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                payload = payload.get("items") or payload.get("files") or []
            files: list[dict[str, Any]] = []
            for item in payload:
                if not isinstance(item, dict) or item.get("type") != "file":
                    continue
                path = item.get("path") or item.get("rfilename")
                if path:
                    files.append({"path": str(path), "size": item.get("size"), "hub": hub})
            if files:
                return files
        except urllib.error.URLError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    return []


def _priority(rel: str) -> int:
    for index, prefix in enumerate(PRIORITY_PREFIXES):
        if rel.replace("\\", "/").startswith(prefix) or rel == prefix.rstrip("/"):
            return index
    if rel.replace("\\", "/").startswith("projects/"):
        return 50
    return 100


def download_file(rel: str, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for hub in _hubs():
        url = f"{hub}{HUB_RESOLVE_PATH}/{rel.replace(chr(92), '/')}"
        req = urllib.request.Request(url, headers={"User-Agent": "AeroBIM-fetch/1.0"})
        digest = hashlib.sha256()
        size = 0
        try:
            with (
                urllib.request.urlopen(req, context=_ssl_context(), timeout=600) as resp,
                dest.open("wb") as handle,
            ):
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            return {"path": rel, "bytes": size, "sha256": digest.hexdigest(), "source": hub}
        except urllib.error.URLError as exc:
            last_error = exc
            continue
    raise last_error or RuntimeError(f"download failed: {rel}")


def _ci_environment() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"


def copy_local(
    src: Path,
    dest: Path,
    *,
    excludes: set[str],
    include_gpl: bool = False,
) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src).as_posix()
        if _is_gpl_path(rel, excludes) and not include_gpl:
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        digest = hashlib.sha256()
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        copied.append(
            {
                "path": rel,
                "bytes": target.stat().st_size,
                "sha256": digest.hexdigest(),
                "source": str(src),
            }
        )
    return copied


def select_files(
    listed: list[dict[str, Any]],
    *,
    excludes: set[str],
    full_non_gpl: bool,
    include_gpl: bool = False,
) -> list[str]:
    chosen: list[str] = []
    for item in sorted(listed, key=lambda row: (_priority(str(row["path"])), str(row["path"]))):
        rel = str(item["path"]).replace("\\", "/")
        if _is_gpl_path(rel, excludes) and not include_gpl:
            continue
        if not full_non_gpl and _priority(rel) >= 50:
            continue
        chosen.append(rel)
    return chosen


def _resolve_from_dir(explicit: Path | None) -> Path | None:
    if explicit is not None and explicit.is_dir():
        return explicit
    for candidate in _local_candidates():
        if (candidate / "questions" / "ifc-bench-v2.csv").is_file():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=None)
    parser.add_argument("--from-dir", type=Path, default=None)
    parser.add_argument("--hub", action="store_true", help="Also try Hugging Face / mirror")
    parser.add_argument(
        "--full-non-gpl",
        action="store_true",
        help="Also download remaining non-GPLv3 project IFC (larger).",
    )
    parser.add_argument(
        "--samolet-demo-copyleft",
        action="store_true",
        help="Opt into Samolet-local copyleft inputs (gitignored .local/ only).",
    )
    parser.add_argument(
        "--include-gplv3",
        action="store_true",
        help="Also copy/download GPLv3 IFC-Bench project dirs. Requires --samolet-demo-copyleft.",
    )
    args = parser.parse_args(argv)
    include_gpl = bool(args.include_gplv3)
    opted_in = bool(args.samolet_demo_copyleft)
    if include_gpl and not local_samolet_demo_copyleft_inputs_permitted(
        opted_in=opted_in, ci=_ci_environment()
    ):
        print(
            "refusing --include-gplv3: need --samolet-demo-copyleft and a non-CI host "
            "(public MIT tree / Docker / other customers stay copyleft-free)",
            file=sys.stderr,
        )
        return 2
    repo = repo_root()
    dest = args.dest or (repo / ".local" / "ifc-bench-v2")
    dest.mkdir(parents=True, exist_ok=True)
    excludes = _load_gpl_excludes(repo)
    downloaded: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    skipped_gpl: list[str] = []
    source = _resolve_from_dir(args.from_dir)
    if source is not None:
        downloaded.extend(copy_local(source, dest, excludes=excludes, include_gpl=include_gpl))
    if args.hub or source is None:
        try:
            listed = list_hub_files()
        except urllib.error.URLError as exc:
            errors.append({"path": "*", "error": str(exc)})
            listed = []
        skipped_gpl = [
            str(item["path"])
            for item in listed
            if _is_gpl_path(str(item["path"]), excludes) and not include_gpl
        ]
        already = {item["path"] for item in downloaded}
        for rel in select_files(
            listed,
            excludes=excludes,
            full_non_gpl=bool(args.full_non_gpl) or include_gpl,
            include_gpl=include_gpl,
        ):
            if rel in already:
                continue
            target = dest / rel
            try:
                downloaded.append(download_file(rel, target))
                print(f"ok {rel} {downloaded[-1]['bytes']}")
            except (urllib.error.URLError, OSError, RuntimeError) as exc:
                errors.append({"path": rel, "error": str(exc)})
                print(f"fail {rel} {exc}")
    payload = {
        "artifact_type": "ifc_bench_v2_fetch",
        "dest": str(dest),
        "from_dir": str(source) if source else None,
        "downloaded": len(downloaded),
        "errors": errors,
        "skipped_gplv3": skipped_gpl,
        "copyleft_lane": "samolet_demo_local" if include_gpl else "public_mit",
        "gplv3_vendored_in_git": False,
        "files": downloaded,
        "claim_boundary": (
            "Local gitignored checkout. "
            + (
                "GPLv3 project dirs included for Samolet-local demo only. "
                if include_gpl
                else "GPLv3 project dirs skipped. "
            )
            + "Not product accuracy. Not 514 false-pass. Not a reason to ship GPL in Docker."
        ),
    }
    (dest / "FETCH_MANIFEST.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: payload[k] for k in ("downloaded", "errors", "from_dir", "skipped_gplv3", "dest")},
            ensure_ascii=False,
        )
    )
    return 0 if downloaded else 1


if __name__ == "__main__":
    raise SystemExit(main())
