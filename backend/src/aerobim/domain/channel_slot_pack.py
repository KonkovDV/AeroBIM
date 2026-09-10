"""Assemble one channel-slot analyze input from files already on disk.

No further customer answers. Not a signed IDS. Not REI60 fixture rules.
Not pack processed. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO
from aerobim.domain.customer_delivery_index import PACK_SLOTS
from aerobim.domain.run_passport import SPF_CAP_BYTES

CLAIM_BOUNDARY: Final = (
    "Operator assemble of one analyze request from files already received. "
    "No further Samolet answers. Unsigned IFC2X3 presence IDS is not their "
    "profile. Fixture REI60 is forbidden. Not product accuracy. "
    "Checkpoint GO; customer_go false."
)

UNSIGNED_IDS_REL: Final = "samples/ids/unsigned-ifc2x3-presence.ids"
FORBIDDEN_IDS_MARKERS: Final[tuple[str, ...]] = (
    "pset_wallcommon",
    "wall-pset-qto",
    "sam-r-001",
)
MAX_DRAWINGS: Final = 64
DEFAULT_DRAWINGS: Final = 8
MAX_DRAWING_BYTES: Final = 32 * 1024 * 1024
_OFFICE = frozenset({".docx", ".doc", ".pdf", ".txt", ".md"})
_PDF = frozenset({".pdf"})
_IFC = frozenset({".ifc"})
_NATIVE = frozenset({".rvt", ".nwd", ".nwc", ".dwg"})
_CALC_TEXT = frozenset({".pdf", ".xlsx", ".xls", ".docx", ".doc", ".txt"})


def assert_slot(slot: str) -> str:
    value = str(slot or "").strip()
    if value not in PACK_SLOTS:
        raise ValueError(f"slot must be one of {PACK_SLOTS}")
    return value


def assert_ids_allowed(ids_path: Path) -> Path:
    resolved = ids_path.resolve()
    name = resolved.name.casefold()
    blob = ""
    try:
        blob = resolved.read_text(encoding="utf-8", errors="replace")[:8000].casefold()
    except OSError as exc:
        raise ValueError(f"IDS unreadable: {exc}") from exc
    haystack = f"{name}\n{blob}"
    for marker in FORBIDDEN_IDS_MARKERS:
        if marker in haystack:
            raise ValueError(
                f"fixture/customer-mismatched IDS is forbidden on channel packs: {marker}"
            )
    if "ifc2x3" not in blob.replace(" ", ""):
        raise ValueError("channel IFC is IFC2X3; IDS must declare IFC2X3")
    return resolved


def _is_ar(path: Path) -> bool:
    name = path.name.upper()
    return "_АР_" in name or "_AP_" in name


def _is_kr(path: Path) -> bool:
    name = path.name.upper()
    return "_КР_" in name or "_KR_" in name


def pick_primary_ifc(
    ifc_paths: Sequence[Path],
    *,
    cap_bytes: int = SPF_CAP_BYTES,
) -> Path:
    files = [path for path in ifc_paths if path.is_file() and path.suffix.lower() in _IFC]
    if not files:
        raise ValueError("no IFC files in slot")
    sized = [(path.stat().st_size, path) for path in files]
    under = [(size, path) for size, path in sized if size <= cap_bytes]
    over = [(size, path) for size, path in sized if size > cap_bytes]
    under_ar = [(size, path) for size, path in under if _is_ar(path)]
    under_kr = [(size, path) for size, path in under if _is_kr(path)]
    if over and any(_is_ar(path) for _, path in over) and under_kr:
        pool = under_kr
    elif under_ar:
        pool = under_ar
    elif under:
        pool = under
    else:
        pool = over
    pool.sort(key=lambda item: (-item[0], item[1].name))
    return pool[0][1]


def pick_drawings(
    files: Sequence[Path],
    *,
    limit: int = DEFAULT_DRAWINGS,
    max_bytes: int = MAX_DRAWING_BYTES,
) -> list[Path]:
    cap = min(MAX_DRAWINGS, max(0, int(limit)))
    pdfs = [
        path
        for path in files
        if path.is_file() and path.suffix.lower() in _PDF and path.stat().st_size <= max_bytes
    ]

    def drawing_rank(path: Path) -> tuple[int, int, str]:
        posix = path.as_posix()
        preferred = 0 if ("02_" in posix or "чертеж" in posix.casefold()) else 1
        return (preferred, path.stat().st_size, path.name)

    pdfs.sort(key=drawing_rank)
    return pdfs[:cap]


def pick_first_existing(files: Sequence[Path], suffixes: frozenset[str]) -> Path | None:
    for path in files:
        if path.is_file() and path.suffix.lower() in suffixes:
            return path
    return None


def discover_slot_files(pack_root: Path) -> dict[str, list[Path]]:
    if not pack_root.is_dir():
        raise ValueError(f"pack root is not a directory: {pack_root}")
    files = [path for path in pack_root.rglob("*") if path.is_file()]
    return {
        "ifc": [path for path in files if path.suffix.lower() in _IFC],
        "pdf": [path for path in files if path.suffix.lower() in _PDF],
        "tz": [
            path
            for path in files
            if path.suffix.lower() in _OFFICE
            and ("0.1" in path.as_posix() or "тз" in path.name.casefold())
        ],
        "calc": [
            path for path in files if "06_" in path.as_posix() and path.suffix.lower() in _CALC_TEXT
        ],
        "native": [path for path in files if path.suffix.lower() in _NATIVE],
        "office_tz": [
            path
            for path in files
            if path.parent.name.startswith("0.1") and path.suffix.lower() in _OFFICE
        ],
    }


def build_package_inventory(*, slot: str, discovered: dict[str, list[Path]]) -> dict[str, Any]:
    assert_slot(slot)
    artifacts: list[dict[str, Any]] = []
    for index, path in enumerate(discovered.get("ifc") or (), start=1):
        artifacts.append(
            {
                "artifact_id": f"ifc-{index}",
                "role": "ifc",
                "stage": "PD",
                "format": "ifc",
                "path_hint": path.name,
            }
        )
    if discovered.get("office_tz") or discovered.get("tz"):
        tz_files = discovered.get("office_tz") or discovered.get("tz") or []
        tz = tz_files[0] if tz_files else None
        if tz is not None:
            artifacts.append(
                {
                    "artifact_id": "tz-1",
                    "role": "technical_spec",
                    "stage": "PD",
                    "format": tz.suffix.lstrip(".").lower() or "pdf",
                    "path_hint": tz.name,
                }
            )
    if discovered.get("calc"):
        artifacts.append(
            {
                "artifact_id": "calc-1",
                "role": "calculation",
                "stage": "PD",
                "format": discovered["calc"][0].suffix.lstrip(".").lower(),
                "path_hint": discovered["calc"][0].name,
                "has_justification": True,
            }
        )
    artifacts.append(
        {
            "artifact_id": "pd-ar",
            "role": "pd_section",
            "discipline": "AR",
            "section_code": "AR",
            "stage": "PD",
            "format": "pdf",
            "cipher": "АР-ПД",
        }
    )
    artifacts.append(
        {
            "artifact_id": "pd-kzh",
            "role": "pd_section",
            "discipline": "KZH",
            "section_code": "KZH",
            "stage": "PD",
            "format": "pdf",
            "cipher": "КЖ-ПД",
        }
    )
    artifacts.append(
        {
            "artifact_id": "pd-pz",
            "role": "pd_section",
            "discipline": "PZ",
            "section_code": "PZ",
            "stage": "PD",
            "format": "pdf",
            "cipher": "ПЗ-ПД",
        }
    )
    for index, path in enumerate(discovered.get("native") or (), start=1):
        artifacts.append(
            {
                "artifact_id": f"native-{index}",
                "role": "other",
                "format": path.suffix.lstrip(".").lower(),
                "path_hint": path.name,
            }
        )
    return {
        "schema": "aerobim_package_inventory_v1",
        "project_id": f"channel-{slot}",
        "mandatory_pd_sections": ["PZ", "AR", "KZH"],
        "require_pd_rd_pairing": True,
        "require_specifications": True,
        "require_schedules": True,
        "require_sheet_ciphers": False,
        "artifacts": artifacts,
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "waiting_for_samolet": False,
        "ids_in_pack": False,
        "rd_ifc_present": False,
    }


def assemble_slot_inputs(
    pack_root: Path,
    *,
    slot: str,
    repo: Path,
    drawing_limit: int = DEFAULT_DRAWINGS,
) -> dict[str, Any]:
    slot = assert_slot(slot)
    discovered = discover_slot_files(pack_root)
    ifc_path = pick_primary_ifc(discovered["ifc"])
    ids_path = assert_ids_allowed(repo / UNSIGNED_IDS_REL)
    tz = pick_first_existing(discovered.get("office_tz") or [], _OFFICE) or pick_first_existing(
        discovered.get("tz") or [], _OFFICE
    )
    calc = pick_first_existing(discovered.get("calc") or [], _CALC_TEXT)
    drawings = pick_drawings(discovered.get("pdf") or [], limit=drawing_limit)
    over_cap = ifc_path.stat().st_size > SPF_CAP_BYTES
    return {
        "slot": slot,
        "ifc_path": ifc_path,
        "ids_path": ids_path,
        "technical_spec_path": tz,
        "calculation_path": calc,
        "drawing_paths": drawings,
        "inventory": build_package_inventory(slot=slot, discovered=discovered),
        "ifc_over_spf_cap": over_cap,
        "native_rejected": sorted({path.suffix.lower() for path in discovered.get("native") or []}),
        "waiting_for_samolet": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "fixture_demo": False,
    }
