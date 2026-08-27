"""Owner-AI execution plan after TZ v1 pin + live-tree triage.

Stages 0–4 from the 2026-08-27 plan. Agent-executable items are scaffolds
and honesty gates. Dual raters, signed appointing-party IDS, QTO export,
federated MEP IFC, and bar entities remain owner-blocked. Checkpoint NO_GO.
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.owner_files_inventory import public_rehearsal_snapshot
from aerobim.domain.signed_oos import oos_snapshot
from aerobim.domain.tz_v1_brief import PAPER_OBJECTS, mik_act_may_cite_tz_v1_accuracy_as_measured

CLAIM_LEVEL: Final = "coverage_map_only"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "Execution of the owner-AI quality plan. Scaffolds and honesty gates, "
    "not criterion validity. Not product accuracy. Not customer SLA. "
    "Not MEP delivered. Checkpoint NO_GO. closes_rt001/002/003=false."
)

DESIGN_TZ_EXTRACTOR_HITS: Final = 0
DESIGN_TZ_EXTRACTOR_STATUS: Final = "extraction_gap"
DEFAULT_IFC_CAP_MIB: Final = 256
MIK_M2_M8: Final = "VERIFY_WITH_OPERATOR"

# Dual-axis: agent can land a brake; owner must supply the missing object.
PLAN_ITEMS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "P0-01",
        "stage": "0",
        "title": "Local files/ inventory under .local/; no pack_hash in git",
        "agent": "done",
        "owner": "keep_nda_out_of_git",
        "stop": "sha256 of the NDA pack in git",
    },
    {
        "id": "P0-02",
        "stage": "0",
        "title": "Pack is PD; RD absent; expertise-after is zip not a loose tree",
        "agent": "done",
        "owner": "n/a",
        "stop": "PD↔RD pairing as if RD IFC exists",
    },
    {
        "id": "P1-QTO",
        "stage": "1",
        "title": "QTO NetFloorArea on IfcSpace or signed qto_space_area OOS",
        "agent": "scaffold",
        "owner": "blocked_export_or_oos",
        "stop": "TEP Does-not from missing QTO",
    },
    {
        "id": "P1-MEP",
        "stage": "1",
        "title": "Federated IOS IFC or signed mep_federated OOS",
        "agent": "scaffold",
        "owner": "blocked_ifc_or_oos",
        "stop": "MEP delivered / RT-003 CLOSED",
    },
    {
        "id": "P1-REBAR",
        "stage": "1",
        "title": "IfcReinforcingBar or signed rebar_class4 OOS; do not parse LIRA",
        "agent": "scaffold",
        "owner": "blocked_bars_or_oos",
        "stop": "pitch pset = class 4 delivered",
    },
    {
        "id": "P1-EXTRACT",
        "stage": "1",
        "title": "Design-TZ extractor 0 hits is extraction_gap, not absent TZ",
        "agent": "done",
        "owner": "n/a",
        "stop": "house TZ has no fire/area requirements",
    },
    {
        "id": "P2-RATERS",
        "stage": "2",
        "title": "Two independent raters + κ/α on a frozen remark set",
        "agent": "protocol_ready",
        "owner": "blocked_raters",
        "stop": "PrecisionClaim.publishable without κ",
    },
    {
        "id": "P2-IDS",
        "stage": "2",
        "title": "Appointing-party IDS with approval_ref + pack_hash (RT-002b)",
        "agent": "protocol_ready",
        "owner": "blocked_signature",
        "stop": "city AGR pack = Samolet customer_approved",
    },
    {
        "id": "P2-PUBLISH",
        "stage": "2",
        "title": "Interim 0.60 protocol until raters + signed profile",
        "agent": "done",
        "owner": "blocked_publishable",
        "stop": "TZ v1 >90% as a product score",
    },
    {
        "id": "P3-GATE",
        "stage": "3",
        "title": "DeterminismGate, AGR≠customer, KR≠KZH, IFC cap 256 MiB",
        "agent": "done",
        "owner": "n/a",
        "stop": "raise cap because one AR is over 256 MiB",
    },
    {
        "id": "P4-KT3",
        "stage": "4",
        "title": "KT#3 speech: four papers unmixed; MIK act = interim 0.60",
        "agent": "done",
        "owner": "n/a",
        "stop": "glue v1 brief / v2 / seven tasks / house TZ",
    },
    {
        "id": "P4-MIK",
        "stage": "4",
        "title": "Fund forms M2/M8 stay VERIFY_WITH_OPERATOR",
        "agent": "done",
        "owner": "blocked_operator_forms",
        "stop": "invent Fund templates",
    },
)

LITERATURE_CALIBRATION: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "L-EGCC",
        "ref": "arXiv:2607.29058",
        "licenses": "four-state Meets/Does-not/Missing/Uncertain + HITL",
        "blocks": "autonomous approve; EGCC % as AeroBIM or IFC score",
    },
    {
        "id": "L-ARCHER",
        "ref": "arXiv:2607.25566",
        "licenses": "deterministic orchestration of generated checkers",
        "blocks": "LLM writes summary.passed",
    },
    {
        "id": "L-SGR",
        "ref": "arXiv:2606.12065",
        "licenses": "geometry-intensive compliance as a research pattern",
        "blocks": "84.3% as fire deliverable on the NDA pack",
    },
    {
        "id": "L-ISHIGAKI",
        "ref": "arXiv:2606.08545",
        "licenses": "validator-in-the-loop IDS draft aid",
        "blocks": "customer_approved from an LLM",
    },
    {
        "id": "L-JUDGE",
        "ref": "arXiv:2606.00093",
        "licenses": "Cohen κ / α with abstention handling; dual humans",
        "blocks": "raw agreement as gold",
    },
    {
        "id": "L-DRAWINGVQA",
        "ref": "arXiv:2607.15418",
        "licenses": "VLM advisory; expert 94.9% vs Gemini 71.7% as literature",
        "blocks": "those % as AeroBIM; TZ tasks 1/3/7 closed",
    },
    {
        "id": "L-AECV",
        "ref": "AECV-Bench 2026",
        "licenses": "OCR strong, symbol counting 0.40–0.55 unsolved",
        "blocks": "CV door/window count as product accuracy",
    },
    {
        "id": "L-IDS-OSS",
        "ref": "IfcTester / Xbim.IDS / ifc-lite / bSI IDS-Audit-tool",
        "licenses": "IDS 1.0 checking engines; license-aware reuse",
        "blocks": "Xbim AGPL silently in the MIT runtime",
    },
)


def _extraction_gap() -> dict[str, Any]:
    return {
        "status": DESIGN_TZ_EXTRACTOR_STATUS,
        "deterministic_hits": DESIGN_TZ_EXTRACTOR_HITS,
        "licensed": (
            "House design TZ uses class II / C0 prose and TEP tables; "
            "fixture patterns expect REI60 / millimetre walls"
        ),
        "blocked": "Project TZ has no fire or area requirements",
        "constructs_unmixed": ("II/C0 ≠ wall EI 45 ≠ door EI30/EI60 ≠ fixture REI60"),
    }


def plan_snapshot() -> dict[str, Any]:
    """Machine-checkable plan pin. Does not close RT."""

    items = [dict(row) for row in PLAN_ITEMS]
    agent_done = sum(1 for row in items if row["agent"] == "done")
    owner_blocked = sum(1 for row in items if row["owner"].startswith("blocked"))
    oos = oos_snapshot()
    inventory = public_rehearsal_snapshot()
    return {
        "artifact_type": "owner_ai_plan_execution",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "paper_objects": list(PAPER_OBJECTS),
        "mik_act_may_cite_tz_v1_accuracy_as_measured": (
            mik_act_may_cite_tz_v1_accuracy_as_measured()
        ),
        "default_ifc_cap_mib": DEFAULT_IFC_CAP_MIB,
        "raise_ifc_cap": False,
        "parse_rvt_nwd_lira": False,
        "seven_task_criterion": "Uncertain",
        "precision_claim_publishable": False,
        "mik_m2_m8": MIK_M2_M8,
        "extraction_gap": _extraction_gap(),
        "oos": {
            "any_accepted": oos["any_accepted"],
            "templates_unsigned": oos["templates_unsigned"],
            "kinds": oos["kinds"],
        },
        "inventory": inventory,
        "literature_calibration": [dict(row) for row in LITERATURE_CALIBRATION],
        "items": items,
        "agent_done_count": agent_done,
        "owner_blocked_count": owner_blocked,
        "item_count": len(items),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "DESIGN_TZ_EXTRACTOR_HITS",
    "DESIGN_TZ_EXTRACTOR_STATUS",
    "LITERATURE_CALIBRATION",
    "PLAN_ITEMS",
    "plan_snapshot",
]
