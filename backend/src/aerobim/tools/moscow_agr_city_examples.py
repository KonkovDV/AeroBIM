"""Shared pin for city-published Moscow AGR example IFCs.

Binaries stay under gitignored ``.local/``. Official IDS/TEP/Vedomost stay in
``samples/``. Does not close RT-001 / RT-002b / RT-003.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from aerobim.tools.benchmark_project_package import repo_root

MANIFEST_REL = Path("samples") / "agr" / "dgp" / "CITY_IFC_MANIFEST.json"
LOCAL_REL = Path(".local") / "moscow-agr-examples"
CLAIM_BOUNDARY = (
    "City-published AGR CIM examples (stroimprosto.mos.ru cim-agr). "
    "Not a PD pack: no sheets, TZ, two revisions, calculations, or expertise "
    "remarks. Not a Samolet-signed profile. Class-1 AGR exchange + official "
    "IDS engine coverage only. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)
CLAIM_LEVEL = "moscow_agr_city_example_rehearsal"


def manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / MANIFEST_REL


def load_manifest(root: Path | None = None) -> dict[str, Any]:
    payload = json.loads(manifest_path(root).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("CITY_IFC_MANIFEST.json must be an object")
    return payload


def local_root(root: Path | None = None) -> Path:
    return (root or repo_root()) / LOCAL_REL


def ifc_dir(root: Path | None = None) -> Path:
    return local_root(root) / "ifc"


def pin_path(root: Path | None = None) -> Path:
    return local_root(root) / "PIN.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ids_paths_for_entry(pack_dir: Path, entry: dict[str, Any]) -> list[Path]:
    """Role-matched official IDS files for one city example IFC."""

    names = [str(name) for name in (entry.get("ids_names") or []) if str(name)]
    return [pack_dir / name for name in names]


ids_paths_for_entry = ids_paths_for_entry


def missing_ifc_files(root: Path | None = None) -> list[str]:
    manifest = load_manifest(root)
    dest = ifc_dir(root)
    missing: list[str] = []
    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("local_name") or "")
        if not name or not (dest / name).is_file():
            missing.append(name or "?")
    return missing
