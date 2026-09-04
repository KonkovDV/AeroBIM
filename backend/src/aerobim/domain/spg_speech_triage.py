"""SPG speech Red Team triage — 2026-09-01.

Consulting notes stay owner speech, not a product and not a jury exhibit.
Path must not contain the hyphenated token blocked by pre-commit.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "SPG August 2026 notes are attributed speech. Construction cut is not SAM. "
    "FM/PM cut is adjacent. PDFs stay off git. Filename stays off TIER0. "
    "Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-SPG-SAM",
        "verdict": "KILL",
        "attack": "Treat the SPG notes or the 10.1 bn BIM TAM as AeroBIM SAM",
        "brake": "K4: TAM attributed; SAM in RUB is empty",
    },
    {
        "id": "RT-SPG-TIM-PACK",
        "verdict": "KILL",
        "attack": "49% TIM among developers means the Samolet pack is measurable",
        "brake": "Pilot TIM is not PD+RD+IFC ready for IDS; RT-001 OPEN",
    },
    {
        "id": "RT-SPG-GLUE-26",
        "verdict": "KILL",
        "attack": "Glue construction TIM 49% to operations BIM 26%",
        "brake": "Two reports, two constructs; do not splice",
    },
    {
        "id": "RT-SPG-FM-SHIP",
        "verdict": "KILL",
        "attack": "Ship a digital-twin / FM line because the 60-page note exists",
        "brake": "TZ is PD/RD verification; FM stays adjacent",
    },
    {
        "id": "RT-SPG-FOREIGN-PCT",
        "verdict": "KILL",
        "attack": "Paste HubEx or WillowTwin percent cuts into A1-A8",
        "brake": "foreign_labor_cut_as_ours False; hours stay empty",
    },
    {
        "id": "RT-SPG-ISUP",
        "verdict": "KILL",
        "attack": "Read 398-r as a KT#3 duty to join customer ISUP/CDE",
        "brake": "TZ 2.2.2 is file exchange; auth BFF stays 501",
    },
    {
        "id": "RT-SPG-PDF-GIT",
        "verdict": "KILL",
        "attack": "Commit the SPG PDFs into the public tree",
        "brake": "Vendor licence forbids copy; not a jury exhibit",
    },
    {
        "id": "RT-SPG-TIER0",
        "verdict": "KILL",
        "attack": "List the consulting pin on TIER0 or hop there from the eight-task card",
        "brake": "Filename off TIER0 and off jury surfaces",
    },
    {
        "id": "RT-SPG-ACCURACY",
        "verdict": "KILL",
        "attack": "Quote SPG aggregates as AeroBIM product accuracy",
        "brake": "detected_count 0; PrecisionClaim.publishable still the only gate",
    },
    {
        "id": "RT-SPG-CAPEX",
        "verdict": "KILL",
        "attack": "Housing starts down means ask the partner to fund AI",
        "brake": "K4 is zero entry, not CAPEX",
    },
    {
        "id": "RT-SPG-RVT",
        "verdict": "KILL",
        "attack": "TIM coverage means native Revit/Navisworks ingest is due",
        "brake": "Exchange stays IFC+PDF/A; natives fail-closed",
    },
    {
        "id": "RT-SPG-ATTR",
        "verdict": "HOLD",
        "attack": "Cite SPG-computed 398-r averages without naming AO SPG",
        "brake": "Vendor asks attribution when using their figures",
    },
    {
        "id": "RT-SPG-KEEP-PIN",
        "verdict": "HOLD",
        "attack": "Delete the owner pin so the 49% brake has nowhere to live",
        "brake": "Keep the pin; keep it off the jury map",
    },
    {
        "id": "RT-SPG-SPLIT",
        "verdict": "ACCEPT",
        "attack": "One SPG brand means one market",
        "brake": "8-page construction vs 60-page FM/PM",
    },
    {
        "id": "RT-SPG-DATA",
        "verdict": "ACCEPT",
        "attack": "TZ silence on XML/infomodel looks like an unmet AI item",
        "brake": "Speech: machine-readable PD/RD first, then models",
    },
    {
        "id": "RT-SPG-ZERO",
        "verdict": "ACCEPT",
        "attack": "Rework-cost pressure is an innovation-budget ask",
        "brake": "K4 speech stays zero entry",
    },
)


def spg_speech_triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "spg_speech_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_sam": False,
        "is_fm_product": False,
        "pdf_in_git": False,
        "on_tier0": False,
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "TRIAGE_ROWS",
    "spg_speech_triage_snapshot",
]
