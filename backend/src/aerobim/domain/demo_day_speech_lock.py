"""Demo-day 21.09.2026 speech lock — Red Team, five seats, licensed numbers.

Pins evidence already in git. Does not close RT-001/002/003.
Does not name sitting members. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.deep_study_facts import PUBLIC_DEEP_STUDY
from aerobim.domain.mik_commission_scoring import (
    FINALIST_CRITERIA,
    TRL_SELF_ASSESS,
    trl_5_claimed,
)
from aerobim.domain.unpack_census import PUBLIC_UNPACK_CENSUS

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Licensed demo-day speech for 2026-09-21. Carrier audit is not pack "
    "processed. Open-bench clash is not customer MEP. AECV macro_extended is "
    "not F1 and not product accuracy. GOST R 58048 self-assess is TRL 4, not 5. "
    "Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
)

EVENT: Final = "techlab_moscow_demo_day"
EVENT_DATES: Final = ("2026-09-21",)
TASK_APPENDIX_4: Final = 6
COMMISSION_NUMBER: Final = 7
DECK_FILE: Final = "AeroBIM_demo_day_2026-09-13"

# Public IDS engine coverage (not a appointing-party-signed profile).
MOEXP_IDS_FILES: Final = 24
MOEXP_IDS_SPECS: Final = 389
SPBEXP_IDS_FILES: Final = 22
SPBEXP_IDS_SPECS: Final = 356
AGR_IDS_FILES: Final = 4
AGR_IDS_SPECS: Final = 102
PUBLIC_IDS_FILES: Final = MOEXP_IDS_FILES + SPBEXP_IDS_FILES + AGR_IDS_FILES
PUBLIC_IDS_SPECS: Final = MOEXP_IDS_SPECS + SPBEXP_IDS_SPECS + AGR_IDS_SPECS

AECV_METRIC: Final = "macro_extended"
AECV_VALUE: Final = 0.4325
AECV_IS_F1: Final = False
AECV_N_FIELD_SCORES_EXTENDED: Final = 585
FIXTURE_EXTRACTION_MACRO_F1: Final = 0.86
POWER_DESIGN_N: Final = 62
RECOMMENDED_N: Final = 111
INTERIM_PRECISION: Final = 0.60
WILSON_STOP_LOWER: Final = 0.50
EXPERIMENT_B_KR_DETECTED: Final = 4
EXPERIMENT_B_KR_N: Final = 24
DUPLEX_CLASH_COUNT: Final = 837
DUPLEX_CORPUS: Final = "open_bench_ifc_bench_duplex"
MOSCOW_CIM_SELFCHECK_START: Final = "2026-06-29"
CHANNEL_IFC_SCHEMA: Final = "IFC2X3"
SPACE_AREA_FROM_GEOMETRY: Final = "not_implemented"
CDE_IMPORT: Final = "NOT_VERIFIED"
AUTH_BFF_DEFAULT: Final = "501_NOT_IMPLEMENTED"
TRL_CLAIMED: Final = 4

SEAT_OPTICS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "mik_piloting_center_chair",
        "optic": "Fund forms: programme → agreement → method → act",
        "licensed": "Ask the Fund operator for M2/M9 forms; partner signs annexes only",
        "kill": "Ask the partner which Fund form closes the grant",
    },
    {
        "id": "mik_demand_center_expert",
        "optic": "Class of buyer, legal entity, IP path, not one-logo custom",
        "licensed": "Zero-CAPEX file exchange; IDS profile is data not a core fork",
        "kill": "Monoproduct for one CDE; Russian-software-registry as a present status",
    },
    {
        "id": "partner_tech_customer_director",
        "optic": "Cycle days, escrow timing, revision delta — not expert-hours",
        "licensed": "E1–E5 unsigned; three multipliers, two of them theirs",
        "kill": "Named delay percentages as our saving; hours without a partner baseline",
    },
    {
        "id": "partner_project_office_lead",
        "optic": "HITL, ADR-001, BCF file, no production-CDE write",
        "licensed": "Default GET /v1/auth/bff is 501; BCF T1 structural; T2 NOT_VERIFIED",
        "kill": "SSO ready; remarks already in their registry; UI role flag as ACL",
    },
    {
        "id": "partner_information_modelling_lead",
        "optic": "Export gaps: empty QTO, grid-less plugin, no rebar, no MEP IFC",
        "licensed": "IfcSpace QTO empty; IfcReinforcingBar 0; MEP entities 0; NWD unread",
        "kill": "Checked MEP/rebar/axes on the transferred IFC; 837 as their AR↔MEP",
    },
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-DEMO-TRL5",
        "verdict": "KILL",
        "attack": "Print УГТ-5 / TRL 5 on the cover as GOST R 58048 readiness",
        "brake": "Self-assess TRL 4; trl_5_claimed False; no dual-rater on partner pack",
    },
    {
        "id": "RT-DEMO-837-CUSTOMER",
        "verdict": "KILL",
        "attack": "Cite 837 IfcClash hits as AR↔MEP on the partner pack",
        "brake": "federated-clash-duplex is IFC-Bench duplex; MEP entities on channel = 0",
    },
    {
        "id": "RT-DEMO-GRID-ALL-PACKS",
        "verdict": "KILL",
        "attack": "Say IfcGrid is missing from the whole channel",
        "brake": "Grid 0 / 13 / 53 by pack; only the EDM export omitted axes",
    },
    {
        "id": "RT-DEMO-AREA-GEOMETRY",
        "verdict": "KILL",
        "attack": "Claim net floor area is computed from IfcSpace geometry",
        "brake": "Inventory reads QTO NetFloorArea only; geometry path not_implemented",
    },
    {
        "id": "RT-DEMO-F1-043",
        "verdict": "KILL",
        "attack": "Call AECV 0.4325 a macro F1",
        "brake": "Publish name is macro_extended; not F1; open_bench_only",
    },
    {
        "id": "RT-DEMO-N62-AS-N",
        "verdict": "KILL",
        "attack": "Cite n≥62 as the signed sample size",
        "brake": "62 is power_design only; recommended_n is 111 (interval width)",
    },
    {
        "id": "RT-DEMO-KR-17",
        "verdict": "KILL",
        "attack": "Round Experiment B KR 4/24 up to 17% on a public slide",
        "brake": "Headline is ≈16.7% (4/24); coverage_map_only, not product recall",
    },
    {
        "id": "RT-DEMO-389-IN-50",
        "verdict": "KILL",
        "attack": "Attribute 389 specifications to all 50 public IDS files",
        "brake": "389 is MOEXP 24 files; 50 files hold 847 specs across three packs",
    },
    {
        "id": "RT-DEMO-SSO-READY",
        "verdict": "KILL",
        "attack": "Promise SSO/OIDC/BFF on their IdP as already live",
        "brake": "Default GET /v1/auth/bff = 501; full SSO remains post-pilot",
    },
    {
        "id": "RT-DEMO-BCF-CDE",
        "verdict": "KILL",
        "attack": "Say findings already land in their CDE registry via BCF",
        "brake": "T1 structural ZIP; cde_import NOT_VERIFIED until T2 log",
    },
    {
        "id": "RT-DEMO-REGISTRY-NOW",
        "verdict": "KILL",
        "attack": "List Russian-software-registry as a present product status",
        "brake": "CLAIMS_LOCK: registry wording forbidden until a legal gap analysis",
    },
    {
        "id": "RT-DEMO-PACK-PROCESSED",
        "verdict": "KILL",
        "attack": "Title the channel pass as findings on their pack / pack processed",
        "brake": "processed False; publishable_finding_count 0; carrier audit only",
    },
    {
        "id": "RT-DEMO-IFC4-EXAMPLE",
        "verdict": "KILL",
        "attack": "Show an unlabeled IFC4 ADD2 finding as a channel result",
        "brake": "Channel IFC is IFC2X3 only; fixture examples must be labeled fixture",
    },
    {
        "id": "RT-DEMO-NWD-NATIVE",
        "verdict": "KILL",
        "attack": "Say three NWD federations were accepted / read natively",
        "brake": "Three federations present as carriers; native NWD is fail-closed",
    },
    {
        "id": "RT-DEMO-REVISION-DUPES",
        "verdict": "KILL",
        "attack": "Cite duplicate revisions as a pinned finding class",
        "brake": "Unpack has 4 IFC copies of wrapper files; finding class not pinned",
    },
    {
        "id": "RT-DEMO-MYPY-FILECOUNT",
        "verdict": "KILL",
        "attack": "Publish a mypy file count that is not in the CI pin",
        "brake": "runtime-baseline attests mypy PASS; file count is not a pin field",
    },
    {
        "id": "RT-DEMO-AGR-DATE",
        "verdict": "KILL",
        "attack": "Date Moscow CIM self-check as 23.06.2026",
        "brake": "Repo pin is 29.06.2026 (stroimprosto / regulatory-baseline)",
    },
    {
        "id": "RT-DEMO-WEIGHTS-PDF",
        "verdict": "KILL",
        "attack": "Cite Appendix 3 weights as attested_by=ci",
        "brake": "PDF not in git; desktop App 3 matches 30/20/20/20/10; not ci",
    },
    {
        "id": "RT-DEMO-ESCROW-NAMED",
        "verdict": "KILL",
        "attack": "Put the partner's own delay % on the problem slide as our effect",
        "brake": "Open market context only; E1–E5 stay unsigned; no named delay as ours",
    },
    {
        "id": "RT-DEMO-UGT-ON-COVER",
        "verdict": "KILL",
        "attack": "Lead the cover with a readiness-level numeral",
        "brake": "Cover: seam + evidence chain. TRL 4 lives in appendix, labeled self-assess",
    },
    {
        "id": "RT-DEMO-AI-NOT-NEEDED",
        "verdict": "KILL",
        "attack": "Say ИИ не нужна as if the product has no model",
        "brake": "ADR-001: deterministic verdict; AI is extraction and hints only",
    },
    {
        "id": "RT-DEMO-VALIDATOR-SURNAME",
        "verdict": "KILL",
        "attack": "Invent a named validator on the P4 slide",
        "brake": "Role is нормоконтроль / ГИП комплекта; no invented surname",
    },
    {
        "id": "RT-DEMO-LEGAL-DATE",
        "verdict": "KILL",
        "attack": "Invent a legal-entity registration date",
        "brake": "Do not mint a юрлицо date; Fund FAQ allows a team of natural persons",
    },
    {
        "id": "RT-DEMO-GANTT",
        "verdict": "KILL",
        "attack": "Show a Gantt as the delivery plan",
        "brake": "Public backlog is GitHub Issues, not a Gantt in this tree",
    },
    {
        "id": "RT-DEMO-SLA-PASS",
        "verdict": "KILL",
        "attack": "Read sla_pass true as customer package SLA",
        "brake": "artifact_type is schema id; claim_level=fixture_only; customer_go false",
    },
    {
        "id": "RT-DEMO-RECALL-100",
        "verdict": "KILL",
        "attack": "Say 100% recall from seam-clean 10/10",
        "brake": "synthetic_only; Wilson lower 0.722; not product recall",
    },
)


def ifcspace_total() -> int:
    pin = PUBLIC_DEEP_STUDY
    return int(pin["ifcspace_pack_a"]) + int(pin["ifcspace_pack_b"]) + int(pin["ifcspace_pack_c"])


def experiment_b_kr_share() -> float:
    return EXPERIMENT_B_KR_DETECTED / EXPERIMENT_B_KR_N


def licensed_slide_lines() -> tuple[str, ...]:
    spaces = ifcspace_total()
    return (
        "We are a pack-acceptance gate, not a model checker.",
        f"GOST R 58048 self-assess is TRL {TRL_SELF_ASSESS}, not 5.",
        f"{spaces} IfcSpace rows; NetFloorArea filled = 0.",
        "IfcGrid is 0 / 13 / 53 by pack; rebar entities = 0; MEP IFC entities = 0.",
        "837 IfcClash hits are IFC-Bench duplex, not the partner pack.",
        "AECV 0.4325 is macro_extended on an open bench, not F1.",
        "Pilot n for interval width is 111; 62 is power design only.",
        "Experiment B KR coverage is 16.7% (4/24), coverage_map_only.",
        "389 specifications sit in 24 MOEXP files; 50 public files hold 847 specs.",
        "BCF 2.1/3.0 ZIP is structural T1; CDE import is NOT_VERIFIED.",
        "Default GET /v1/auth/bff is 501. Space area from geometry is not implemented.",
        "Channel IFC schema is IFC2X3. Three NWD federations are unread carriers.",
        "processed is false. customer_go is false. LLM does not write summary.passed.",
        "P3 metric is cross-file discrepancy count per pack before examination.",
        "Verdict is deterministic; AI is extraction and hints only (ADR-001).",
        "Do not invent a validator surname or a legal-entity registration date.",
        "Backlog is GitHub Issues, not a Gantt.",
        "sla_pass true is fixture p95, not customer SLA.",
        "Seam-clean 10/10 is synthetic_only; not product recall.",
    )


def demo_day_speech_lock_snapshot() -> dict[str, Any]:
    pin = PUBLIC_DEEP_STUDY
    census = PUBLIC_UNPACK_CENSUS
    b_weights = tuple(row[1] for row in FINALIST_CRITERIA)
    return {
        "artifact_type": "demo_day_speech_lock",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "customer_go": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_pack_processed": False,
        "event": EVENT,
        "event_dates": list(EVENT_DATES),
        "task_appendix_4": TASK_APPENDIX_4,
        "commission_number": COMMISSION_NUMBER,
        "deck_file": DECK_FILE,
        "trl_self_assess": TRL_SELF_ASSESS,
        "trl_5_claimed": trl_5_claimed(),
        "trl_claimed_on_cover": False,
        "ifc_schema": CHANNEL_IFC_SCHEMA,
        "ifcspace_total": ifcspace_total(),
        "netfloorarea_count": int(pin["netfloorarea_count"]),
        "ifcgrid_by_pack": [
            int(pin["ifcgrid_pack_a"]),
            int(pin["ifcgrid_pack_b_ar"]),
            int(pin["ifcgrid_pack_c_ar"]),
        ],
        "ifcreinforcingbar_count": int(pin["ifcreinforcingbar_count"]),
        "mep_duct_pipe_cable_count": int(pin["mep_duct_pipe_cable_count"]),
        "nwd_federation_count": int(pin["nwd_federation_count"]),
        "nwd_native": "NOT_IMPLEMENTED",
        "space_area_from_geometry": SPACE_AREA_FROM_GEOMETRY,
        "unpacked_ifc_count": int(census["unpacked_ifc_count"]),
        "unpacked_ifc_are_wrapper_copies": bool(census["unpacked_ifc_are_wrapper_copies"]),
        "revision_duplicate_finding_class_pinned": bool(
            census["revision_duplicate_finding_class_pinned"]
        ),
        "duplex_clash_count": DUPLEX_CLASH_COUNT,
        "duplex_corpus": DUPLEX_CORPUS,
        "aecv_metric": AECV_METRIC,
        "aecv_value": AECV_VALUE,
        "aecv_is_f1": AECV_IS_F1,
        "aecv_n_field_scores_extended": AECV_N_FIELD_SCORES_EXTENDED,
        "fixture_extraction_macro_f1": FIXTURE_EXTRACTION_MACRO_F1,
        "power_design_n": POWER_DESIGN_N,
        "recommended_n": RECOMMENDED_N,
        "interim_precision": INTERIM_PRECISION,
        "wilson_stop_lower": WILSON_STOP_LOWER,
        "experiment_b_kr_detected": EXPERIMENT_B_KR_DETECTED,
        "experiment_b_kr_n": EXPERIMENT_B_KR_N,
        "moexp_ids_files": MOEXP_IDS_FILES,
        "moexp_ids_specs": MOEXP_IDS_SPECS,
        "public_ids_files": PUBLIC_IDS_FILES,
        "public_ids_specs": PUBLIC_IDS_SPECS,
        "moscow_cim_selfcheck_start": MOSCOW_CIM_SELFCHECK_START,
        "cde_import": CDE_IMPORT,
        "auth_bff_default": AUTH_BFF_DEFAULT,
        "finalist_weights_attributed": list(b_weights),
        "weights_pdf_in_git": False,
        "mypy_file_count_in_ci_pin": False,
        "names_in_git": False,
        "licensed_slide_lines": list(licensed_slide_lines()),
        "seats": [dict(row) for row in SEAT_OPTICS],
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
    }


__all__ = [
    "AECV_IS_F1",
    "AECV_METRIC",
    "AECV_VALUE",
    "CLAIM_BOUNDARY",
    "DUPLEX_CLASH_COUNT",
    "DUPLEX_CORPUS",
    "PUBLIC_IDS_FILES",
    "PUBLIC_IDS_SPECS",
    "RECOMMENDED_N",
    "SEAT_OPTICS",
    "SPACE_AREA_FROM_GEOMETRY",
    "TRIAGE_ROWS",
    "TRL_CLAIMED",
    "demo_day_speech_lock_snapshot",
    "experiment_b_kr_share",
    "ifcspace_total",
    "licensed_slide_lines",
]
