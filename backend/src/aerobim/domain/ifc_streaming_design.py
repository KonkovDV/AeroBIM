
"""IFC streaming / disk R-tree — designed, not implemented.

SPF ``ifcopenshell.open`` stays 256 MiB. Files up to 1.5 GB convert to
IfcOpenShell RocksDB. In-memory ``IfcSpatialIndex`` is not a disk R-tree.
This module is the honesty brake against treating a design note as a
raised ``AEROBIM_MAX_IFC_BYTES`` default.
"""

from __future__ import annotations

from typing import Final

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
)
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_size_policy import (
    ROCKSDB_BACKEND_STATUS,
    SPF_RAM_MULTIPLIER_LITERATURE,
    SPF_RAM_MULTIPLIER_SOURCE,
    size_policy_snapshot,
)

CLAIM_BOUNDARY: Final = (
    "Streaming IFC parser and disk R-tree are designed, not implemented. "
    "SPF in-memory open stays 256 MiB. Files up to 1.5 GB use RocksDB. "
    "In-memory IfcSpatialIndex is not a disk R-tree. JSON sidecar is dump_only. "
    "WASM stays 256 MiB. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

DEFAULT_ANALYZE_IFC_BYTES: Final = DEV_DEFAULT_UPLOAD_BYTES
STREAMING_PARSER_STATUS: Final = "designed_not_implemented"
DISK_RTREE_STATUS: Final = "designed_not_implemented"


def streaming_design_snapshot() -> dict[str, object]:
    """Honesty snapshot: design exists; default analyze cap is unchanged."""

    return {
        "artifact_type": "ifc_streaming_disk_rtree_design",
        "claim_level": "coverage_map_only",
        "checkpoint": CHECKPOINT,
        "streaming_parser": STREAMING_PARSER_STATUS,
        "disk_r_tree": DISK_RTREE_STATUS,
        "in_memory_spatial_index": True,
        "spatial_index_json_sidecar": "dump_only",
        "default_analyze_bytes": DEFAULT_ANALYZE_IFC_BYTES,
        "stated_model_ingest_bytes": SAMOLET_STATED_MODEL_BYTES,
        "raises_default_cap": False,
        "spf_ram_multiplier_literature": SPF_RAM_MULTIPLIER_LITERATURE,
        "spf_ram_multiplier_source": SPF_RAM_MULTIPLIER_SOURCE,
        "rocksdb_backend": ROCKSDB_BACKEND_STATUS,
        "size_policy": size_policy_snapshot(),
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "next_slice": (
            "Persist AABB R-tree on disk; keep WASM at 256 MiB; "
            "OA-16 RSS on a local over-SPF file is still owner-local"
        ),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "DEFAULT_ANALYZE_IFC_BYTES",
    "DISK_RTREE_STATUS",
    "STREAMING_PARSER_STATUS",
    "streaming_design_snapshot",
]
