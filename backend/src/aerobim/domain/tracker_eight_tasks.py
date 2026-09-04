
"""Eight KT#3 tracker tasks assigned 29.08.2026.

Distinct from the six 14.08 tasks in ``tracker_six_tasks``. Git closes
engineering hygiene; it does not send mail, inventory a customer channel, or
mint product accuracy. Personal names stay out of this snapshot.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.core.security.upload_limits import (
    DEV_DEFAULT_UPLOAD_BYTES,
    SAMOLET_STATED_MODEL_BYTES,
)
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.system_capabilities import build_auth_bff_capability

CLAIM_LEVEL: Final = "operational_hygiene"
CLAIM_BOUNDARY: Final = (
    "Eight tracker tasks (29.08.2026). Finding volume is not accuracy. "
    "SIG-01 report phrase: объём находок на канале получен. "
    "Customer pack stays out of git until a written data-handling order. "
    "SPF in-memory open stays 256 MiB; 1.5 GB is ingest + RocksDB. "
    "auth_bff default remains NOT_IMPLEMENTED. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)
SIG01_REPORT_PHRASE: Final = "объём находок на канале получен"
ASSIGNED_AT: Final = "2026-08-29"
KT3_WINDOW: Final = "2026-09-03..2026-09-21"
FEATURE_FREEZE: Final = "2026-09-18"
SAMOLET_APPENDIX4_TASK: Final = 6
COMMISSION_ORDER_NUMBER: Final = 7
CADSOFTTOOLS_USD_RETRIEVED_2026_08_30: Final = 765

TRACKER_EIGHT: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "SIG-01",
        "title": "Run on Samolet IFC/PDF; finding volume + type breakdown",
        "git": "volume_taxonomy_and_lite_cli",
        "owner": "blocked_channel_pack",
        "show": "python -m aerobim.tools.run_finding_volume --findings-lite-dir <local>",
        "stop": "Finding count as product accuracy, pack processed, or customer defect list",
    },
    {
        "id": "SIG-02",
        "title": "Inventory the 43 GB pack (format / processed / priority / legal flag)",
        "git": "pack_probe_and_archive_overlap",
        "owner": "blocked_data_regime",
        "show": "pack_probe + pack_archive_overlap + census/deep-study pins",
        "stop": "Commit names, hashes, or '43 GB processed'",
    },
    {
        "id": "SIG-03",
        "title": "External contour: closed storage + Expert/User roles",
        "git": "roles_in_api_bff_501",
        "owner": "blocked_production_idp",
        "show": "GET /v1/auth/bff → 501; expert/user aliases in auth_roles",
        "stop": "Lab cookie path as production SSO",
    },
    {
        "id": "SIG-04",
        "title": "Two-criterion accuracy + draft typical-error classifier",
        "git": "catalog_ge_20_unconfirmed",
        "owner": "blocked_dual_rater",
        "show": "samples/benchmarks/samolet-typical-errors-catalog.json",
        "stop": "Treat unsigned catalog as customer-confirmed; mix fixture F1 with channel volume",
    },
    {
        "id": "SIG-05",
        "title": "Question pack to Samolet via organizers",
        "git": "draft_in_partners",
        "owner": "blocked_send_mail",
        "show": "docs/partners/SAMOLET_QUESTION_PACK_KT3_2026_08.md",
        "stop": "Republish the share URL; treat TBD as write-from-scratch",
    },
    {
        "id": "SIG-06",
        "title": "LIRA compare: effort and KT#3 feasibility",
        "git": "four_checks_partial",
        "owner": "blocked_calculation_notes",
        "show": "docs/quality/CALCULATION_COMPARE_FOUR_CHECKS_2026_09.md",
        "stop": "Independent solver / native .lir",
    },
    {
        "id": "SIG-07",
        "title": "Position on RVT/NWD and computer vision",
        "git": "osint_onepager",
        "owner": "blocked_legal_entity_license",
        "show": "docs/quality/FORMAT_INGEST_TRIAGE_2026_09.md",
        "stop": "Sustaining 7500 USD = BimRv; stale CADSoftTools list price; DWG-ready",
    },
    {
        "id": "SIG-08",
        "title": "Datasets: RUT (MIIT) via IT mentor",
        "git": "letter_not_in_git",
        "owner": "blocked_send_mail",
        "show": "docs/OWNER_ACTIONS_2026_09.md OA-10",
        "stop": "Teaching pack closes RT-001",
    },
)


def tracker_eight_snapshot() -> dict[str, Any]:
    auth = build_auth_bff_capability()
    items = [dict(row) for row in TRACKER_EIGHT]
    return {
        "artifact_type": "tracker_eight_tasks_kt3",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "assigned_at": ASSIGNED_AT,
        "kt3_window": KT3_WINDOW,
        "feature_freeze": FEATURE_FREEZE,
        "samolet_appendix4_task": SAMOLET_APPENDIX4_TASK,
        "commission_order_number": COMMISSION_ORDER_NUMBER,
        "spf_analyze_cap_bytes": DEV_DEFAULT_UPLOAD_BYTES,
        "ingest_cap_bytes": SAMOLET_STATED_MODEL_BYTES,
        "raises_spf_default_for_ingest": False,
        "cadsofttools_usd_retrieved": CADSOFTTOOLS_USD_RETRIEVED_2026_08_30,
        "cadsofttools_stale_list_price": True,
        "rt002a": "CLOSED",
        "rt002b": "OPEN",
        "auth_bff_status": auth["status"],
        "finding_volume_is_accuracy": False,
        "sig01_report_phrase": SIG01_REPORT_PHRASE,
        "sig01_publishable_finding_count": 0,
        "channel_max_pass": "channel_local_max_pass_snapshot",
        "pack_family_facts": "pack_family_snapshot",
        "customer_pack_in_git": False,
        "space_efficiency_kt3": "advisory_unsigned",
        "space_efficiency_delivered": False,
        "items": items,
        "item_count": len(items),
        "owner_blocked_count": sum(1 for row in items if row["owner"].startswith("blocked")),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "SIG01_REPORT_PHRASE",
    "TRACKER_EIGHT",
    "tracker_eight_snapshot",
]
