"""Git-safe unpack-tree family facts (31.08.2026).

Counts and booleans only. Uncompressed GiB stays out of git (OA-9).
Not pack processed. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Unpack-tree family facts after the 31.08 live walk. File counts and "
    "booleans only. Uncompressed byte totals stay out of git. Not pack "
    "processed. Not a LIRA solver. Not CC-2 MATCH. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)

# Named calc-complex extensions (not garbled numeric sidecars).
LIRA_NAMED_EXT: Final[frozenset[str]] = frozenset(
    {
        ".lir",
        ".~lir",
        ".~~lir",
        ".f74",
        ".f74a",
        ".f74m",
        ".f74s",
        ".ald",
        ".cfa",
        ".rib",
        ".spr",
        ".slt12",
        ".hlt12",
        ".scadmodelcolor",
    }
)

PUBLIC_PACK_FAMILY: Final[dict[str, Any]] = {
    "study_date": "2026-08-31",
    "unpack_file_count": 6408,
    "live_walk_matched_evening_pin": True,
    "calc_binaries_majority_of_unpack_bytes": True,
    "uncompressed_gib_in_git": False,
    "lira_named_ext_file_count": 235,
    "pdf_file_count": 2046,
    "pdf_vector_count": 1318,
    "pdf_scan_like_count": 728,
    "dwg_file_count": 1877,
    "dxf_file_count": 321,
    "dxf_all_ascii": True,
    "rvt_file_count": 75,
    "navis_file_count": 8,
    "max_file_count": 164,
    "office_file_count": 579,
    "office_ooxml_count": 295,
    "office_ole_count": 284,
    "unpack_ifc_copies": 4,
    "unique_ifc_already_analyzed": 15,
    "objects_runnable_complete": 2,
    "tz_class_2_rd_files": 0,
    "docx_with_class_phrase": 6,
    "xlsx_with_load_token": 46,
    "customer_confirmed_patterns": 0,
    "names_in_git": False,
    "hashes_in_git": False,
    "processed": False,
    "parse_lira": False,
    "is_cc2_match": False,
}


def pack_family_snapshot() -> dict[str, Any]:
    return {
        "artifact_type": "pack_family_facts",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        **PUBLIC_PACK_FAMILY,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "LIRA_NAMED_EXT",
    "PUBLIC_PACK_FAMILY",
    "pack_family_snapshot",
]
