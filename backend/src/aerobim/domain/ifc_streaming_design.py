"""IFC streaming / disk R-tree — designed, not implemented.

Full-file ``ifcopenshell.open`` + in-memory ``IfcSpatialIndex`` remain the
analyze path. This module is the honesty brake against treating a design
note as a raised ``AEROBIM_MAX_IFC_BYTES`` default or a live on-disk R-tree.
"""

from __future__ import annotations

from typing import Final

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
)

CLAIM_BOUNDARY: Final = (
    "Streaming IFC parser and disk R-tree are designed, not implemented. "
    "Default analyze cap stays 256 MiB. Stated 1.5 GB is ingest only. "
    "In-memory IfcSpatialIndex is not a disk R-tree. JSON sidecar is dump_only. "
    "Checkpoint NO_GO."
)

DEFAULT_ANALYZE_IFC_BYTES: Final = DEV_DEFAULT_UPLOAD_BYTES
STREAMING_PARSER_STATUS: Final = "designed_not_implemented"
DISK_RTREE_STATUS: Final = "designed_not_implemented"


def streaming_design_snapshot() -> dict[str, object]:
    """Honesty snapshot: design exists; default analyze cap is unchanged."""

    return {
        "artifact_type": "ifc_streaming_disk_rtree_design",
        "claim_level": "coverage_map_only",
        "checkpoint": "NO_GO",
        "streaming_parser": STREAMING_PARSER_STATUS,
        "disk_r_tree": DISK_RTREE_STATUS,
        "in_memory_spatial_index": True,
        "spatial_index_json_sidecar": "dump_only",
        "default_analyze_bytes": DEFAULT_ANALYZE_IFC_BYTES,
        "stated_model_ingest_bytes": SAMOLET_STATED_MODEL_BYTES,
        "raises_default_cap": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "next_slice": (
            "Stream STEP entities; persist AABB R-tree keyed by GUID on disk; "
            "measure RSS before any default-cap change"
        ),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "DEFAULT_ANALYZE_IFC_BYTES",
    "DISK_RTREE_STATUS",
    "STREAMING_PARSER_STATUS",
    "streaming_design_snapshot",
]
