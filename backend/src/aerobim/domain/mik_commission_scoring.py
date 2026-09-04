"""Attributed MIK commission scoring — arithmetic, not a predicted AeroBIM score.

Owner briefing 2026-08-29 of Fund order P-01-OD-52-1/26 (17.06.2026).
The Fund PDF is not in git. Weights are IUA over that briefing, not a
CI-attested pin and not a prize forecast.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).

Does not close RT-001 / RT-002 / RT-003. Does not name sitting members.
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "attributed_program_arithmetic"
CLAIM_BOUNDARY: Final = (
    "Attributed TechLab commission weights. Selection uses the order "
    "protocol form (K1-K5). Regulation Appendix 3 (final table) is not in "
    "git. Not a predicted AeroBIM total. Checkpoint GO "
    "(regulatory_measurement_mvp); customer_go false."
)

ORDER_ID: Final = "П-01-ОД-52-1/26"
ORDER_DATE: Final = "2026-06-17"
ATTESTED_BY: Final = "owner_briefing"

# Max points, System A (Appendix 2 / protocol of the 17.06.2026 order). Sum is 100.
CRITERIA: Final[tuple[tuple[str, int, str], ...]] = (
    ("K1", 40, "team_competence_and_balance"),
    ("K2", 20, "novelty_and_technological_readiness"),
    ("K3", 15, "fit_to_partner_program_tasks"),
    ("K4", 15, "commercialisation_and_scale"),
    ("K5", 10, "work_plan_feasibility"),
)

# System A = Regulation Appendix 2, recovered from the order protocol form.
# System B weights below are an owner briefing of the order, NOT Regulation
# Appendix 3 (final criteria). That appendix has not been seen.
FINALIST_CRITERIA: Final[tuple[tuple[str, int, str], ...]] = (
    ("B1", 30, "fit_to_partner_task_and_requirements"),
    ("B2", 20, "prototype_quality_and_confirmed_metrics"),
    ("B3", 20, "integration_and_deployment_readiness"),
    ("B4", 20, "measurable_partner_effect"),
    ("B5", 10, "documentation_and_handoff"),
)

PRIZE_FLOOR: Final = 50
MAX_TOTAL: Final = 100
# Order p.2.1 selection = mean; p.2.2 final = sum of scores. Different maths.
AGGREGATION: Final = "arithmetic_mean"
FINALIST_AGGREGATION: Final = "sum"
QUORUM_MIN_MEMBERS: Final = 3
NOMINAL_SEATS: Final = 5
MIK_STAFF_SEATS: Final = 2
PARTNER_SEATS_BY_AGREEMENT: Final = 3
PARTNER_NOMINAL_CRITERIA: Final[tuple[str, ...]] = ("K1", "K3", "K5")
MIK_STAFF_NOMINAL_CRITERIA: Final[tuple[str, ...]] = ("K2", "K4")
TIE_BREAK_ORDER: Final[tuple[str, ...]] = ("K3", "K4")
FINALIST_TIE_BREAK_ORDER: Final[tuple[str, ...]] = ("B1",)
FINAL_ROUND_WIDER_THAN_NOMINAL: Final = True
# Attributed: Appendix 4 lists the Partner task as №6; commission №7.
# Historical handout "07" in filenames is not the regulation number.
TASK_APPENDIX_4_NUMBER: Final = 6
COMMISSION_NUMBER: Final = 7
HANDOUT_LABEL: Final = "07"

# Public LETI reprint of Appendix 4 (30.04.2026): row 6 = Partner task.
APPENDIX_4_PUBLIC_SOURCE: Final = (
    "https://new.etu.ru/ru/home/nauka/konkursy-i-granty-na-provedenie-niokr/"
    "konkursy-i-granty-na-provedenie-nauchno-issledovatelskih-rabot/"
    "programma-dorabotki-i-vnedreniya-naukoemkih-ii-reshenij"
)
CITY_PILOT_URL: Final = "https://i.moscow/pilot"
GOST_42001_CARD: Final = "https://protect.gost.ru/gost/details/3cb023c3-e628-45ad-b233-65e3d175eb10"
EVIDENCE_MAP: Final = "docs/quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md"
K1_ROLE_MATRIX_TEMPLATE: Final = "docs/partners/K1_ROLE_MATRIX_TEMPLATE_2026_08.md"
LEVERS_PAST_50: Final = "docs/quality/MIK_A_LEVERS_PAST_50_2026_08.md"
TRL_SELF_ASSESS_DOC: Final = "docs/quality/TRL_GOST_R_58048_SELF_ASSESS_2026.md"
K3_FIT_TICKSHEET: Final = "docs/quality/K3_PARTNER_FIT_TICKSHEET_2026_08.md"
K4_COMMERCIAL_PATH: Final = "docs/quality/K4_COMMERCIAL_PATH_2026_08.md"
K2_NOVELTY_VS_PEERS: Final = "docs/quality/K2_NOVELTY_VS_PEERS_2026_08.md"
PNST_841_MAP: Final = "docs/quality/PNST_841_AI_QUALITY_EVAL_2026.md"
SEAT_BRIEFS: Final = "docs/quality/MIK_SEAT_BRIEFS_2026_08.md"
SEAT_PLAYBOOK: Final = "docs/quality/MIK_COMMISSION_SEAT_PLAYBOOK_2026_09.md"
MIK_OPERATOR_LETTER: Final = "docs/partners/MIK_OPERATOR_LETTER_REQUEST_2026_09.md"
APPLICATION_PASTE: Final = "docs/partners/I_MOSCOW_APPLICATION_PASTE_2026_08.md"
SIGNREADY_COVER: Final = "docs/partners/PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md"
CUSTOMER_THRESHOLDS: Final = "docs/quality/CUSTOMER_THRESHOLD_VS_ACTUAL_2026_08.md"
B_FINAL_TICKSHEET: Final = "docs/quality/B_FINAL_SCORING_TICKSHEET_2026_09.md"
LAB_BEFORE_AFTER: Final = "docs/partners/BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md"
DEFECT_INJECTION_PLAN: Final = "docs/evidence/DEFECT_INJECTION_RECALL_PLAN_2026_09.md"
ADR_004_PRIZE_IP: Final = "docs/architecture/ADR-004-prize-ip-mit-fork-2026.md"
ORDER_WEIGHTS_VERIFICATION: Final = "docs/quality/ORDER_WEIGHTS_VERIFICATION_2026_09.md"
OWNER_ACTIONS: Final = "docs/OWNER_ACTIONS_2026_09.md"
# LETI: not less than 1, not more than 10. K1 scores two competency classes.
MIN_TEAM_SIZE: Final = 1
MAX_TEAM_SIZE: Final = 10
TRL_PROGRAM_FLOOR: Final = 3
TRL_SELF_ASSESS: Final = 4

# Percent of a criterion's maximum (0-20 very low … 81-100 very high).
PERCENT_BANDS: Final[tuple[tuple[int, int, str], ...]] = (
    (0, 20, "very_low"),
    (21, 40, "low"),
    (41, 60, "medium"),
    (61, 80, "high"),
    (81, 100, "very_high"),
)

SEAT_ROLES: Final[tuple[str, ...]] = (
    "mik_piloting_center_chair",
    "mik_demand_center_expert",
    "partner_tech_customer_director",
    "partner_project_office_lead",
    "partner_information_modelling_lead",
)


def criteria_max(code: str) -> int:
    for item_code, points, _name in CRITERIA:
        if item_code == code:
            return points
    raise KeyError(code)


def partner_nominal_criteria_weight() -> int:
    """Nominal max points on partner-attributed seats (K1+K3+K5). Not a forecast."""

    return sum(criteria_max(code) for code in PARTNER_NOMINAL_CRITERIA)


def mik_staff_nominal_criteria_weight() -> int:
    """Nominal max points on Fund staff seats (K2+K4). Not a forecast."""

    return sum(criteria_max(code) for code in MIK_STAFF_NOMINAL_CRITERIA)


def finalist_criteria_max(code: str) -> int:
    for item_code, points, _name in FINALIST_CRITERIA:
        if item_code == code:
            return points
    raise KeyError(code)


def confirmed_partner_validation_metrics() -> bool:
    """B2 'confirmed metrics from testing/validation' on the Partner corpus."""

    return False


def partner_kpis_agreed_in_writing() -> bool:
    """B1 Partner-agreed KPI. TZ >90% is not a signed measurement contract."""

    return False


def points_at_percent(max_points: int, percent: float) -> float:
    if percent < 0 or percent > 100:
        raise ValueError("percent must be 0..100")
    return max_points * percent / 100.0


def k1_low_band_points() -> tuple[float, float]:
    """K1 in the 'low' percent band (21-40% of 40)."""

    return (points_at_percent(40, 21), points_at_percent(40, 40))


def rest_high_band_points() -> tuple[float, float]:
    """K2+K3+K4+K5 (60) in the 'high' percent band (61-80%)."""

    return (points_at_percent(60, 61), points_at_percent(60, 80))


def low_k1_high_rest_total() -> tuple[float, float]:
    """Scenario range. Not a forecast of this team's score."""

    k1_lo, k1_hi = k1_low_band_points()
    rest_lo, rest_hi = rest_high_band_points()
    return (k1_lo + rest_lo, k1_hi + rest_hi)


def prize_floor_automatic_in_low_k1_high_rest() -> bool:
    lo, _hi = low_k1_high_rest_total()
    return lo >= PRIZE_FLOOR


def reachable_inside_low_k1_if_rest_high() -> bool:
    """Top of K1-low + bottom of rest-high is ≥ prize floor. Not a forecast."""

    k1_hi = k1_low_band_points()[1]
    rest_lo = rest_high_band_points()[0]
    return k1_hi + rest_lo >= PRIZE_FLOOR


def k1_ten_people_required() -> bool:
    """LETI: team size 1–10. Two competency classes, not a headcount of 10."""

    return False


def k3_equals_validation_metrics() -> bool:
    """K3 is partner-fit. B2 is protocols plus confirmed partner metrics."""

    return False


def trl_5_claimed() -> bool:
    """Lab self-assess is TRL 4. Partner-environment TRL 5 is not claimed."""

    return False


def k4_revenue_claimed() -> bool:
    """K4 path is not booked revenue or a second signed contract."""

    return False


def pnst_841_certified() -> bool:
    """PNST 841 mapping is not a SQuaRE conformity assessment."""

    return False


def foreign_labor_cut_as_ours() -> bool:
    """Published 72% analog is not AeroBIM or partner hours."""

    return False


def sponsor_quote_is_commission_chair() -> bool:
    """Public task-page sponsor quote is not the attested chair."""

    return False


def tam_horizon_is_our_revenue() -> bool:
    """SPbPU BIM 25.1 bn RUB by 2030 is not AeroBIM revenue or SAM."""

    return False


def regulation_appendix_3_in_git() -> bool:
    """Regulation Appendix 3 (final criteria table) has not been seen."""

    return False


def finalist_weights_are_regulation_appendix_3() -> bool:
    """B1-B5 in this module are an order briefing, not the unseen table."""

    return False


def k4_asks_customer_capex() -> bool:
    """K4 speech is zero-entry / pay-on-result, not a CAPEX ask."""

    return False


def k4_offsets_partner_ifrs_loss() -> bool:
    """Partner 1H2026 IFRS loss is context, not an AeroBIM saving claim."""

    return False


def ras_ifrs_signs_are_the_same() -> bool:
    """Stand-alone RAS +31% revenue is not group IFRS -31%."""

    return False


def catalog_four_are_all_applicants() -> bool:
    """Four catalog cards are not the full applicant set for this task."""

    return False


def peer_card_claims_externally_verified() -> bool:
    """Neighbor catalog claims are not treated as audited public fact."""

    return False


def prize_floor_denominator_known() -> bool:
    """Final prize floor 50: max of the unseen Regulation App 3 is unknown."""

    return False


def predicted_aerobim_total() -> int | None:
    """No licensed numeric forecast. Git does not score the application."""

    return None


def git_raises_k1() -> bool:
    """Empty role-matrix template is not a scored roster."""

    return False


def gost_42001_certified() -> bool:
    """GOST R ISO/IEC 42001 mapping is not a certified AI management system."""

    return False


def city_pilot_is_techlab_prize() -> bool:
    """i.moscow/pilot (city grant, legal entity) is not the TechLab 2M prize."""

    return False


def scoring_snapshot() -> dict[str, Any]:
    lo, hi = low_k1_high_rest_total()
    return {
        "artifact_type": "mik_commission_scoring",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "attested_by": ATTESTED_BY,
        "order_id": ORDER_ID,
        "order_date": ORDER_DATE,
        "fund_pdf_in_git": False,
        "criteria": [
            {"code": code, "max_points": points, "name": name} for code, points, name in CRITERIA
        ],
        "max_total": MAX_TOTAL,
        "prize_floor": PRIZE_FLOOR,
        "aggregation": AGGREGATION,
        "finalist_aggregation": FINALIST_AGGREGATION,
        "quorum_min_members": QUORUM_MIN_MEMBERS,
        "nominal_seats": NOMINAL_SEATS,
        "mik_staff_seats": MIK_STAFF_SEATS,
        "partner_seats_by_agreement": PARTNER_SEATS_BY_AGREEMENT,
        "partner_seats_guaranteed": False,
        "tie_break_order": list(TIE_BREAK_ORDER),
        "novelty_in_tie_break": False,
        "final_round_wider_than_nominal": FINAL_ROUND_WIDER_THAN_NOMINAL,
        "percent_bands": [
            {"lo": lo_b, "hi": hi_b, "label": label} for lo_b, hi_b, label in PERCENT_BANDS
        ],
        "seat_roles": list(SEAT_ROLES),
        "k1_low_band_points": list(k1_low_band_points()),
        "rest_high_band_points": list(rest_high_band_points()),
        "low_k1_high_rest_total": [lo, hi],
        "prize_floor_automatic_in_low_k1_high_rest": (prize_floor_automatic_in_low_k1_high_rest()),
        "predicted_aerobim_total": None,
        "k2_plus_k5_max": 30,
        "application_roster_is_k1_object": True,
        "oral_advisors_score_k1": False,
        "system_a": "regulation_appendix_2_via_order_protocol_form",
        "system_b": "regulation_appendix_3_unseen",
        "finalist_criteria": [
            {"code": code, "max_points": points, "name": name}
            for code, points, name in FINALIST_CRITERIA
        ],
        "finalist_tie_break_order": list(FINALIST_TIE_BREAK_ORDER),
        "task_appendix_4_number": TASK_APPENDIX_4_NUMBER,
        "commission_number": COMMISSION_NUMBER,
        "handout_label": HANDOUT_LABEL,
        "speak_handout_label_as_regulation": False,
        "confirmed_partner_validation_metrics": (confirmed_partner_validation_metrics()),
        "partner_kpis_agreed_in_writing": partner_kpis_agreed_in_writing(),
        "exclusive_rights_may_transfer_under_6_3": True,
        "working_prize_floor": PRIZE_FLOOR,
        "prize_floor_wording_is_ambiguous": True,
        "git_raises_k1": git_raises_k1(),
        "gost_42001_certified": gost_42001_certified(),
        "city_pilot_is_techlab_prize": city_pilot_is_techlab_prize(),
        "appendix_4_public_source": APPENDIX_4_PUBLIC_SOURCE,
        "city_pilot_url": CITY_PILOT_URL,
        "gost_42001_card": GOST_42001_CARD,
        "criterion_evidence_map": EVIDENCE_MAP,
        "k1_role_matrix_template": K1_ROLE_MATRIX_TEMPLATE,
        "levers_past_50": LEVERS_PAST_50,
        "trl_self_assess_doc": TRL_SELF_ASSESS_DOC,
        "k3_fit_ticksheet": K3_FIT_TICKSHEET,
        "min_team_size": MIN_TEAM_SIZE,
        "max_team_size": MAX_TEAM_SIZE,
        "k1_ten_people_required": k1_ten_people_required(),
        "k3_equals_validation_metrics": k3_equals_validation_metrics(),
        "trl_program_floor": TRL_PROGRAM_FLOOR,
        "trl_self_assess": TRL_SELF_ASSESS,
        "trl_5_claimed": trl_5_claimed(),
        "reachable_inside_low_k1_if_rest_high": (reachable_inside_low_k1_if_rest_high()),
        "independent_ogt_performed": False,
        "k4_commercial_path": K4_COMMERCIAL_PATH,
        "k2_novelty_vs_peers": K2_NOVELTY_VS_PEERS,
        "pnst_841_map": PNST_841_MAP,
        "seat_briefs": SEAT_BRIEFS,
        "seat_playbook": SEAT_PLAYBOOK,
        "mik_operator_letter": MIK_OPERATOR_LETTER,
        "partner_nominal_criteria_weight": partner_nominal_criteria_weight(),
        "mik_staff_nominal_criteria_weight": mik_staff_nominal_criteria_weight(),
        "application_paste": APPLICATION_PASTE,
        "signready_cover": SIGNREADY_COVER,
        "k4_revenue_claimed": k4_revenue_claimed(),
        "pnst_841_certified": pnst_841_certified(),
        "foreign_labor_cut_as_ours": foreign_labor_cut_as_ours(),
        "sponsor_quote_is_commission_chair": sponsor_quote_is_commission_chair(),
        "tam_horizon_is_our_revenue": tam_horizon_is_our_revenue(),
        "regulation_appendix_3_in_git": regulation_appendix_3_in_git(),
        "finalist_weights_are_regulation_appendix_3": (
            finalist_weights_are_regulation_appendix_3()
        ),
        "k4_asks_customer_capex": k4_asks_customer_capex(),
        "k4_offsets_partner_ifrs_loss": k4_offsets_partner_ifrs_loss(),
        "ras_ifrs_signs_are_the_same": ras_ifrs_signs_are_the_same(),
        "catalog_four_are_all_applicants": catalog_four_are_all_applicants(),
        "peer_card_claims_externally_verified": (peer_card_claims_externally_verified()),
        "prize_floor_denominator_known": prize_floor_denominator_known(),
        "customer_thresholds": CUSTOMER_THRESHOLDS,
        "b_final_ticksheet": B_FINAL_TICKSHEET,
        "lab_before_after": LAB_BEFORE_AFTER,
        "defect_injection_plan": DEFECT_INJECTION_PLAN,
        "adr_004_prize_ip": ADR_004_PRIZE_IP,
        "order_weights_verification": ORDER_WEIGHTS_VERIFICATION,
        "owner_actions": OWNER_ACTIONS,
    }


__all__ = [
    "AGGREGATION",
    "ATTESTED_BY",
    "CHECKPOINT",
    "CLAIM_BOUNDARY",
    "CRITERIA",
    "B_FINAL_TICKSHEET",
    "CUSTOMER_THRESHOLDS",
    "LAB_BEFORE_AFTER",
    "DEFECT_INJECTION_PLAN",
    "ADR_004_PRIZE_IP",
    "ORDER_WEIGHTS_VERIFICATION",
    "OWNER_ACTIONS",
    "FINALIST_AGGREGATION",
    "FINALIST_CRITERIA",
    "FINALIST_TIE_BREAK_ORDER",
    "PRIZE_FLOOR",
    "TIE_BREAK_ORDER",
    "confirmed_partner_validation_metrics",
    "criteria_max",
    "partner_nominal_criteria_weight",
    "mik_staff_nominal_criteria_weight",
    "finalist_criteria_max",
    "k1_low_band_points",
    "low_k1_high_rest_total",
    "partner_kpis_agreed_in_writing",
    "points_at_percent",
    "predicted_aerobim_total",
    "prize_floor_automatic_in_low_k1_high_rest",
    "reachable_inside_low_k1_if_rest_high",
    "rest_high_band_points",
    "scoring_snapshot",
    "city_pilot_is_techlab_prize",
    "git_raises_k1",
    "gost_42001_certified",
    "k1_ten_people_required",
    "k3_equals_validation_metrics",
    "k4_revenue_claimed",
    "pnst_841_certified",
    "foreign_labor_cut_as_ours",
    "sponsor_quote_is_commission_chair",
    "tam_horizon_is_our_revenue",
    "regulation_appendix_3_in_git",
    "finalist_weights_are_regulation_appendix_3",
    "k4_asks_customer_capex",
    "k4_offsets_partner_ifrs_loss",
    "ras_ifrs_signs_are_the_same",
    "catalog_four_are_all_applicants",
    "peer_card_claims_externally_verified",
    "prize_floor_denominator_known",
    "trl_5_claimed",
]
