"""Owner-disk files/ inventory — local only, never a git pack_hash.

Stage 0 of the owner-AI plan. Scans extension/size presence. Does not parse
IFC, does not emit project names into a git-tracked path, does not raise
the 256 MiB analyze cap.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

DEFAULT_IFC_CAP_BYTES: Final = 256 * 1024 * 1024
CHECKPOINT: Final = "NO_GO"
CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Local owner-disk inventory of files/. Extension and size counts only. "
    "Not TP/FP. Not product accuracy. Not a customer pack_hash. "
    "Checkpoint NO_GO. closes_rt001/002/003=false."
)

# Dated rehearsal pin for git. Live scan may differ; names never enter git.
PUBLIC_REHEARSAL: Final[dict[str, Any]] = {
    "rehearsal_date": "2026-08-27",
    "pack_folder_count": 4,
    "file_count": 2383,
    "ifc_count": 15,
    "ifc_over_default_cap_count": 1,
    "native_rvt_count": 27,
    "calc_binary_count": 24,
    "pdf_count": 1127,
    "dwg_count": 470,
    "dxf_count": 57,
    "names_in_git": False,
    "hashes_in_git": False,
    "rd_ifc_present": False,
    "federated_mep_ifc_present": False,
    "default_ifc_cap_mib": 256,
    "raise_cap": False,
}

_CALC_SUFFIXES: Final[frozenset[str]] = frozenset({".lir", ".spr"})
_NATIVE_BIM_SUFFIXES: Final[frozenset[str]] = frozenset({".rvt", ".nwd", ".nwc"})


def output_is_local_only(repo: Path, output: Path) -> bool:
    """True if output is outside the repo or under repo/.local/."""

    resolved = output.resolve()
    repo_res = repo.resolve()
    try:
        rel = resolved.relative_to(repo_res)
    except ValueError:
        return True
    posix = rel.as_posix()
    return posix == ".local" or posix.startswith(".local/")


def require_local_only_output(repo: Path, output: Path) -> None:
    if not output_is_local_only(repo, output):
        raise ValueError(
            "owner-files inventory must write under <repo>/.local/ "
            "(or outside the git tree); never docs/, samples/, or backend/"
        )


def _iter_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


def scan_owner_files(
    root: Path,
    *,
    ifc_cap_bytes: int = DEFAULT_IFC_CAP_BYTES,
    include_names: bool = False,
) -> dict[str, Any]:
    """Count files by suffix. Names are opt-in and must stay out of git."""

    if not root.is_dir():
        return {
            "status": "SKIPPED_NO_TREE",
            "root_present": False,
            "claim_level": CLAIM_LEVEL,
            "checkpoint": CHECKPOINT,
            "closes_rt001": False,
            "closes_rt002": False,
            "closes_rt003": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "detected_count": 0,
        }
    files = _iter_files(root)
    suffixes: Counter[str] = Counter()
    ifc_sizes: list[int] = []
    pack_folders = sorted(path.name for path in root.iterdir() if path.is_dir())
    nested_pack_folders: list[str] = []
    if len(pack_folders) == 1:
        only = root / pack_folders[0]
        nested_pack_folders = sorted(
            path.name for path in only.iterdir() if path.is_dir()
        )
    for path in files:
        suffix = path.suffix.casefold()
        suffixes[suffix] += 1
        if suffix == ".ifc":
            ifc_sizes.append(path.stat().st_size)
    payload: dict[str, Any] = {
        "status": "SCANNED_LOCAL",
        "root_present": True,
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "pack_folder_count": len(nested_pack_folders) or len(pack_folders),
        "file_count": len(files),
        "ifc_count": suffixes.get(".ifc", 0),
        "ifc_over_default_cap_count": sum(
            1 for size in ifc_sizes if size > ifc_cap_bytes
        ),
        "native_rvt_count": suffixes.get(".rvt", 0),
        "native_navis_count": suffixes.get(".nwd", 0) + suffixes.get(".nwc", 0),
        "calc_binary_count": sum(suffixes[ext] for ext in _CALC_SUFFIXES),
        "pdf_count": suffixes.get(".pdf", 0),
        "dwg_count": suffixes.get(".dwg", 0),
        "dxf_count": suffixes.get(".dxf", 0),
        "names_in_payload": bool(include_names),
        "hashes_in_payload": False,
        "default_ifc_cap_bytes": ifc_cap_bytes,
        "raise_cap": False,
        "by_suffix_top": dict(suffixes.most_common(16)),
        "parse_rvt_nwd_lira": False,
    }
    if include_names:
        payload["pack_folder_labels"] = nested_pack_folders or pack_folders
    return payload


def public_rehearsal_snapshot() -> dict[str, Any]:
    """Git-safe pin. No folder names, no file hashes."""

    return {
        "artifact_type": "owner_files_public_rehearsal",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        **dict(PUBLIC_REHEARSAL),
    }


def rehearsal_differs(scan: Mapping[str, Any]) -> bool:
    """True when a live scan disagrees with the dated public pin on counts."""

    if scan.get("status") != "SCANNED_LOCAL":
        return False
    keys = (
        "pack_folder_count",
        "file_count",
        "ifc_count",
        "ifc_over_default_cap_count",
        "native_rvt_count",
        "calc_binary_count",
        "pdf_count",
        "dwg_count",
        "dxf_count",
    )
    return any(scan.get(key) != PUBLIC_REHEARSAL.get(key) for key in keys)


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "DEFAULT_IFC_CAP_BYTES",
    "PUBLIC_REHEARSAL",
    "output_is_local_only",
    "public_rehearsal_snapshot",
    "rehearsal_differs",
    "require_local_only_output",
    "scan_owner_files",
]
