"""SIG-01 channel Red Team triage — 2026-08-31.

Attacks on the local IFC/PDF rerun after ALL matching. Not RT CLOSED.
Totals, names, hashes, and GUIDs of the channel pack stay .local (OA-9).
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.finding_volume import REPORT_PHRASE, VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE
from aerobim.domain.target_ref import UNRESTRICTED_ELEMENT_MISMATCH_CAP
from aerobim.domain.unsigned_rule_overlap import overlap_groups

CLAIM_LEVEL: Final = "pack_volume_not_accuracy"
CLAIM_BOUNDARY: Final = (
    "SIG-01 channel Red Team triage after the ALL matching fix. "
    "Report phrase: объём находок на канале получен. "
    "Not product accuracy. Not pack processed. Not a customer defect list. "
    "Unsigned ALL+eq is not SP. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

# Verdict is KILL / HOLD / ACCEPT. Brake is the speech or code stop.
TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-SIG01-ACCURACY",
        "verdict": "KILL",
        "attack": "Quote the raw machine-record total as product accuracy or F1",
        "brake": "volume_from_findings is_accuracy False; publishable_finding_count 0",
    },
    {
        "id": "RT-SIG01-DEFECT",
        "verdict": "KILL",
        "attack": "Call the channel volume a Samolet defect list",
        "brake": "is_customer_defect_list False; REPORT_PHRASE only",
    },
    {
        "id": "RT-SIG01-PACK",
        "verdict": "KILL",
        "attack": "15/15 IFC ran through the engine so the pack is processed",
        "brake": "is_pack_processed False; SIG-02 census processed False",
    },
    {
        "id": "RT-SIG01-SP",
        "verdict": "KILL",
        "attack": "Unsigned ALL+eq REI60 is an SP 2.13130 / SP 63 check",
        "brake": "samolet-*-rules and SAM-AR template are synthetic; RT-002c OPEN",
    },
    {
        "id": "RT-SIG01-EI45",
        "verdict": "KILL",
        "attack": "Observed wall FireRating EI 45 vs demo REI60 is a fire fail",
        "brake": "IUA SAM-09; firerating_wall_class_observed EI 45; not TZ II/C0",
    },
    {
        "id": "RT-SIG01-CAP-RAISE",
        "verdict": "KILL",
        "attack": "Raise UNRESTRICTED_ELEMENT_MISMATCH_CAP to publish a full defect list",
        "brake": "Cap 50 is the honesty bound; suppressor is coverage_unsigned not defects",
    },
    {
        "id": "RT-SIG01-SUPPRESS-N",
        "verdict": "KILL",
        "attack": "Quote 'N further mismatches suppressed' as N customer defects",
        "brake": "suppressed_remainder_is_finding_count False; phrase not a defect list",
    },
    {
        "id": "RT-SIG01-EQ-AS-DETECT",
        "verdict": "KILL",
        "attack": "Count capped ALL+eq rows as element_detection_unsigned findings",
        "brake": "unrestricted_eq_sample class; GUID on a cap sample is not a named hit",
    },
    {
        "id": "RT-SIG01-OVERLAP",
        "verdict": "KILL",
        "attack": "Sum REQ-FIRE-001 and SAM-AR-011 (same wall FireRating) as two defects",
        "brake": "unsigned_rule_overlap groups; exists+eq on one key is one property",
    },
    {
        "id": "RT-SIG01-KR-DOOR",
        "verdict": "KILL",
        "attack": "Entity-presence 'no IfcDoor' on a KR file is missing doors as a defect",
        "brake": "entity_presence class; pack A is 6 AR + 5 KR; discipline split",
    },
    {
        "id": "RT-SIG01-PDF-HITL",
        "verdict": "KILL",
        "attack": "PDF HITL rows are drawing findings or a CV door/window count",
        "brake": "service_hitl; drawing_annotation_count 0 on the sample; IUA SAM-03",
    },
    {
        "id": "RT-SIG01-PDF-GIT",
        "verdict": "KILL",
        "attack": "Commit HITL sheet names, GUIDs, or channel totals into git",
        "brake": "OA-9; require_local_only_output; names_in_git False",
    },
    {
        "id": "RT-SIG01-QTO-TEP",
        "verdict": "KILL",
        "attack": "NetFloorArea missing on IfcSpace is a TEP Does-not",
        "brake": "coverage_unsigned; netfloorarea_count 0; Missing QTO ≠ TEP",
    },
    {
        "id": "RT-SIG01-SLA",
        "verdict": "KILL",
        "attack": "RocksDB elapsed on the over-cap IFC is a customer SLA measurement",
        "brake": "thresholds publishable_sla false; IUA SAM-06 protocol_planning only",
    },
    {
        "id": "RT-SIG01-MEP",
        "verdict": "KILL",
        "attack": "Clash-capability skip without federated MEP is MEP delivered or failed",
        "brake": "service_capability; mep_system_clash NOT_VERIFIED; RT-003 OPEN",
    },
    {
        "id": "RT-SIG01-IDS",
        "verdict": "KILL",
        "attack": "The unsigned fire/structure/AR packs close RT-002",
        "brake": "RT-002a city IDS ≠ RT-002b Samolet signature; closes_rt002 false",
    },
    {
        "id": "RT-SIG01-F1",
        "verdict": "KILL",
        "attack": "Volume classes are dual-rater precision or a typical-error catalog",
        "brake": "customer_confirmed_patterns 0; SIG-04 still needs two raters",
    },
    {
        "id": "RT-SIG01-RAIL",
        "verdict": "KILL",
        "attack": "SAM-AR-020 Height ≥ 1.2 m is an SP railing check",
        "brake": "Demo threshold in the AR template; unrestricted_eq_sample",
    },
    {
        "id": "RT-SIG01-ALL-FIX",
        "verdict": "ACCEPT",
        "attack": "target_ref ALL still means an element named ALL",
        "brake": "is_unrestricted_target_ref; ALL walks every instance of ifc_entity",
    },
    {
        "id": "RT-SIG01-GUID-FIX",
        "verdict": "ACCEPT",
        "attack": "A 22-character IfcPropertySingleValue.Name is a duplicate GlobalId",
        "brake": "spf_entity_first_attr_is_global_id default-deny IfcRoot allowlist",
    },
    {
        "id": "RT-SIG01-EXISTS-FIX",
        "verdict": "ACCEPT",
        "attack": "exists on ALL still passes when one of N instances has the property",
        "brake": "missing on N of M coverage row; one filled IfcSpace does not close ALL",
    },
)


def triage_snapshot() -> dict[str, object]:
    groups = overlap_groups()
    return {
        "artifact_type": "sig01_channel_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "report_phrase": REPORT_PHRASE,
        "is_accuracy": False,
        "is_pack_processed": False,
        "is_customer_defect_list": False,
        "publishable_finding_count": 0,
        "unrestricted_eq_sample_class": VOLUME_CLASS_UNRESTRICTED_EQ_SAMPLE,
        "mismatch_cap": UNRESTRICTED_ELEMENT_MISMATCH_CAP,
        "unsigned_overlap_group_count": len(groups),
        "channel_totals_in_git": False,
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "TRIAGE_ROWS",
    "triage_snapshot",
]
