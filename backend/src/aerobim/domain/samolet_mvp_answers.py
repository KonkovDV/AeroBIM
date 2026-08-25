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

SAMOLET_ANSWERS_RECEIVED_AT = "2026-08-25"


def samolet_mvp_answers_payload() -> dict[str, object]:
    """Static honesty block for ``/v1/system/capabilities``."""

    return {
        "received_at": SAMOLET_ANSWERS_RECEIVED_AT,
        "source": "docs/partners/",
        "share_url_received": True,
        "share_ingested_in_git": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "checkpoint": "NO_GO",
        "stated_office_bytes": SAMOLET_STATED_OFFICE_BYTES,
        "stated_model_bytes": SAMOLET_STATED_MODEL_BYTES,
        "dev_default_upload_bytes": DEV_DEFAULT_UPLOAD_BYTES,
        "analyze_ifc_default_bytes": DEV_DEFAULT_UPLOAD_BYTES,
        "wasm_viewer_cap_bytes": WASM_IFC_VIEWER_CAP_BYTES,
        "native_rvt_nwd": "not_implemented",
        "ifc_required": "IFC 2x3 and newer as exported by the authoring tool",
        "mvp_roles": {
            "expert": "HITL reviewer alias (validate/edit remarks)",
            "user": "viewer alias (reports and analytics; no HITL under pilot/production)",
        },
        "cde_integration_mvp": False,
        "https_required": True,
        "peak_packs_per_day_mvp": "5-10",
        "horizontal_scale_required_on_mvp": False,
        "calculation_compare": (
            "cross-document compare of declared LIRA PDF/Excel vs RD/BIM; not a solver"
        ),
        "space_efficiency": (
            "customer definition recorded; signed sellable-area thresholds absent; "
            "advisory inventory only"
        ),
        "remark_shape": "essence + norm/STO clause (never invented) + location detail",
    }


__all__ = [
    "SAMOLET_ANSWERS_RECEIVED_AT",
    "samolet_mvp_answers_payload",
]
