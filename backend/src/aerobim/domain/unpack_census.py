
"""Git-safe suffix/magic census of the local unpack tree.

Live scan writes under ``.local/`` only. This pin is counts, not a pack_hash,
not TP/FP, not «processed». Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Local wrapper + unpack-tree suffix/magic census. Evening recensus "
    "after deleting covered source archives (0 zip/7z left). Not pack "
    "processed. Not product accuracy. Not native RVT/DWG/LIRA. SPF cap "
    "stays 256 MiB. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

# Dated pin for git. Live trees may grow; names and hashes never enter git.
# Tracker task SIG-02 still uses the phrase «43 GB» as the assigned title —
# that is not this measurement.
PUBLIC_UNPACK_CENSUS: Final[dict[str, Any]] = {
    "census_date": "2026-08-30",
    "census_pass": "evening",
    "wrapper_file_count": 2552,
    "unpacked_file_count": 6408,
    "morning_wrapper_file_count": 2618,
    "morning_unpacked_file_count": 6467,
    "source_archives_deleted_after_coverage": True,
    "wrapper_ifc_count": 15,
    "unpacked_ifc_count": 4,
    "ifc_schema": "IFC2X3",
    "ifc_over_spf_cap_count": 1,
    "wrapper_pdf_count": 1208,
    "unpacked_pdf_count": 2046,
    "pdf_named_png_wrapper": 1,
    "pdf_named_png_unpacked": 2,
    "wrapper_dwg_count": 551,
    "unpacked_dwg_count": 1877,
    "wrapper_dxf_count": 67,
    "unpacked_dxf_count": 321,
    "wrapper_rvt_count": 27,
    "unpacked_rvt_count": 75,
    "wrapper_navis_count": 21,
    "unpacked_navis_count": 8,
    "wrapper_lir_count": 20,
    "unpacked_lir_count": 36,
    "wrapper_lir_tilde_count": 21,
    "unpacked_lir_tilde_count": 89,
    "unpacked_max_count": 164,
    "unpacked_empty_count": 30,
    "wrapper_zip_count": 0,
    "wrapper_sevenzip_count": 0,
    "unpacked_zip_shells": 0,
    "unpacked_sevenzip_shells": 0,
    "public_rehearsal_file_count_2026_08_27": 2383,
    "names_in_git": False,
    "hashes_in_git": False,
    "processed": False,
    "raise_cap": False,
    "parse_rvt_nwd_lira": False,
    "default_ifc_cap_mib": 256,
}


def unpack_census_snapshot() -> dict[str, Any]:
    return {
        "artifact_type": "unpack_census",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        **PUBLIC_UNPACK_CENSUS,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "PUBLIC_UNPACK_CENSUS",
    "unpack_census_snapshot",
]
