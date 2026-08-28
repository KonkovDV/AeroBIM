"""Honesty snapshot of Samolet questionnaire answers (2026-08-25).

Does not close RT-001/002/003. Share URL is not a hashed customer pack.
"""

from __future__ import annotations

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
    SAMOLET_STATED_OFFICE_BYTES,
    WASM_IFC_VIEWER_CAP_BYTES,
)
from aerobim.domain.calculation_table_compare import table_compare_honesty_snapshot
from aerobim.domain.ifc_streaming_design import streaming_design_snapshot
from aerobim.domain.spec_volume_compare import spec_volume_honesty_snapshot

SAMOLET_ANSWERS_RECEIVED_AT = "2026-08-25"
SAMOLET_TEAM_BRIEF_RECEIVED_AT = "2026-08-26"


def samolet_mvp_answers_payload() -> dict[str, object]:
    """Static honesty block for ``/v1/system/capabilities``."""

    return {
        "received_at": SAMOLET_ANSWERS_RECEIVED_AT,
        "team_brief_received_at": SAMOLET_TEAM_BRIEF_RECEIVED_AT,
        "share_url_received": True,
        "share_ingested_in_git": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "checkpoint": "NO_GO",
        "dataset_classes": [
            "tz",
            "dwg",
            "ifc",
            "calculations",
            "scans",
            "typical_errors",
        ],
        "stated_office_bytes": SAMOLET_STATED_OFFICE_BYTES,
        "stated_model_bytes": SAMOLET_STATED_MODEL_BYTES,
        "dev_default_upload_bytes": DEV_DEFAULT_UPLOAD_BYTES,
        "analyze_ifc_default_bytes": DEV_DEFAULT_UPLOAD_BYTES,
        "wasm_viewer_cap_bytes": WASM_IFC_VIEWER_CAP_BYTES,
        "native_rvt_nwd": "not_implemented",
        "native_dwg": "not_implemented",
        "native_lir": "not_implemented",
        "raster_scans": "optional_ocr_not_labeled_corpus",
        "ifc_required": "IFC 2x3 and newer as exported by the authoring tool",
        "mvp_roles": {
            "expert": "HITL reviewer alias (validate/edit remarks)",
            "user": "viewer alias (reports and analytics; no HITL under pilot/production)",
        },
        "cde_integration_mvp": False,
        "https_required": True,
        "customer_stated_closed_cloud": True,
        "speech_forbid_no_customer_data": True,
        "axis_nearest_grid_intersection": False,
        "peak_packs_per_day_mvp": "5-10",
        "horizontal_scale_required_on_mvp": False,
        "calculation_compare": (
            "cross-document compare of declared LIRA PDF/Excel vs RD/BIM; not a solver"
        ),
        "calculation_table_compare": table_compare_honesty_snapshot(),
        "spec_volume_compare": spec_volume_honesty_snapshot(),
        "ifc_streaming": streaming_design_snapshot(),
        "space_efficiency": (
            "customer definition recorded; signed sellable-area thresholds absent; "
            "advisory inventory only"
        ),
        "remark_shape": (
            "essence + norm/STO clause (never invented) + location "
            "(storey/axis from IfcSpatialIndex when present; else explicit missing)"
        ),
    }


__all__ = [
    "SAMOLET_ANSWERS_RECEIVED_AT",
    "SAMOLET_TEAM_BRIEF_RECEIVED_AT",
    "samolet_mvp_answers_payload",
]
