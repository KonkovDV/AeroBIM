"""Maximum licensed pass on a local NDA copy (31.08.2026).

What git plus a gitignored quarantine copy can do vs TZ v2, TechLab seven
comparison tasks, MIK speech, and tracker SIG-01…08. Not a customer
verdict. Not a jury exhibit. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.channel_pack_triage import pack_triage_snapshot
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.deep_study_facts import deep_study_snapshot
from aerobim.domain.pack_family_facts import pack_family_snapshot
from aerobim.domain.tracker_eight_tasks import tracker_eight_snapshot
from aerobim.domain.unpack_census import unpack_census_snapshot
from aerobim.domain.unsigned_rule_overlap import overlap_snapshot

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Maximum pass on a local NDA copy: inventory, unsigned-pack volume "
    "shape, carrier presence. Not product accuracy. Not pack processed. "
    "Not statutory PP-87. Not Meets/Does-not on seven TechLab tasks. "
    "Not native RVT/NWD/.lir. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

# Agent can land these on the local copy. Owner still owns mail, IdP, raters.
AGENT_CAN_RUN: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "SIG-01",
        "run": "run_finding_volume --findings-lite-dir (local rerun)",
        "licensed": "объём находок на канале получен; publishable_finding_count=0",
        "stop": "raw machine count as accuracy / customer defects",
    },
    {
        "id": "SIG-02",
        "run": "pack_probe + pack_archive_overlap + census/deep-study pins",
        "licensed": "format / processed_now / priority / legal_flag aggregates",
        "stop": "43 GB processed; names or hashes in git",
    },
    {
        "id": "SIG-04",
        "run": "catalog ≥20 + channel_carrier_observations",
        "licensed": "observed classes on carriers; customer_confirmed_patterns=0",
        "stop": "unsigned catalog as customer-accepted",
    },
    {
        "id": "SIG-06",
        "run": "token presence on office/PDF + CC-2/CC-4 methodology",
        "licensed": "B25/B35/ЛИРА bytes present; not a solver",
        "stop": "конструкции пересчитаны; native .lir parsed",
    },
)

AGENT_CANNOT: Final[tuple[str, ...]] = (
    "Send SIG-05 / OA-10 mail",
    "Production OIDC BFF (SIG-03 stays 501)",
    "Dual raters / κ (SIG-04 owner)",
    "Raise AEROBIM_MAX_IFC_BYTES / SPF 256 MiB",
    "Parse RVT/NWD/.lir",
    "Ingest local checklists into confirmed patterns",
    "Commit pack names, hashes, GUIDs, sheet titles",
    "Statutory PP-87 completeness certificate",
    "TEP / space-efficiency Does-not from missing QTO",
    "Commit uncompressed byte totals of the NDA tree",
    "Treat token shortlists as CC-2/CC-4 MATCH",
)

TECHLAB_SEVEN: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "1",
        "title": "PD/RD ↔ AGR sheets / TEP",
        "on_pack": "PD sheet ciphers coindex IFC; RD absent; NetFloorArea 0",
        "criterion": "Uncertain",
    },
    {
        "id": "2",
        "title": "PD ↔ typical albums / EIR",
        "on_pack": "Standard tree + EIR workbook present; customer_approved IDS absent",
        "criterion": "Uncertain",
    },
    {
        "id": "3",
        "title": "OPR/PD/RD layouts",
        "on_pack": "IfcSpace present; QTO absent; pack A IfcGrid 0",
        "criterion": "Uncertain",
    },
    {
        "id": "4",
        "title": "Layouts ↔ IRD / design TZ / STU",
        "on_pack": "Design TZ II/C0 vs wall FireRating EI 45; extractor hits 0",
        "criterion": "Uncertain",
    },
    {
        "id": "5",
        "title": "AR/KR/fire/tech/MEP vs each other",
        "on_pack": "AR+KR IFC; no federated MEP IFC; unsigned fire/structure overlap",
        "criterion": "Uncertain",
    },
    {
        "id": "6",
        "title": "Resubmission ↔ outstanding remarks",
        "on_pack": "Expertise-after is zip not a loose tree; OEP xlsx is one judge",
        "criterion": "Uncertain",
    },
    {
        "id": "7",
        "title": "Reinforcement drawings ↔ calculation maps",
        "on_pack": "IfcReinforcingBar 0; .lir present not parsed; CC-1 blocked on IFC",
        "criterion": "Uncertain",
    },
)

TZ_CARRIER_STOPS: Final[tuple[str, ...]] = (
    "NetFloorArea / Qto_SpaceBaseQuantities = 0",
    "IfcReinforcingBar = 0",
    "MEP duct/pipe/cable IFC = 0",
    "Wall FireRating when filled = EI 45, not TZ II/C0, not demo REI60",
    "Pack is PD; RD pairing off",
    "Engine mandatory KZH ≠ pack KR label",
    "space_efficiency stays advisory_unsigned",
)


def channel_local_max_pass_snapshot() -> dict[str, Any]:
    tracker = tracker_eight_snapshot()
    family = pack_family_snapshot()
    triage = pack_triage_snapshot()
    return {
        "artifact_type": "channel_local_max_pass",
        "as_of": "2026-08-31",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "publishable_finding_count": 0,
        "finding_volume_is_accuracy": False,
        "pack_processed": False,
        "sig01_report_phrase": tracker["sig01_report_phrase"],
        "owner_blocked_count": tracker["owner_blocked_count"],
        "feature_freeze": tracker["feature_freeze"],
        "auth_bff_status": tracker["auth_bff_status"],
        "spf_analyze_cap_mib": 256,
        "raises_spf_default": False,
        "customer_confirmed_patterns": 0,
        "space_efficiency_kt3": tracker["space_efficiency_kt3"],
        "agent_can_run": [dict(row) for row in AGENT_CAN_RUN],
        "agent_cannot": list(AGENT_CANNOT),
        "techlab_seven": [dict(row) for row in TECHLAB_SEVEN],
        "tz_carrier_stops": list(TZ_CARRIER_STOPS),
        "unpack_census": unpack_census_snapshot(),
        "deep_study": deep_study_snapshot(),
        "pack_family": family,
        "pack_triage_kill_count": triage["kill_count"],
        "pack_triage_hold_count": triage["hold_count"],
        "pack_triage_accept_count": triage["accept_count"],
        "uncompressed_gib_in_git": False,
        "unsigned_overlap": overlap_snapshot(),
        "tracker_eight": tracker,
        "local_outputs_dir": ".local/pack-out/ (gitignored)",
        "names_in_git": False,
        "hashes_in_git": False,
    }


__all__ = [
    "AGENT_CANNOT",
    "AGENT_CAN_RUN",
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "TECHLAB_SEVEN",
    "channel_local_max_pass_snapshot",
]
