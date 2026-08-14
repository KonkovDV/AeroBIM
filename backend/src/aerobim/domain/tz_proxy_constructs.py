"""Construct-validity map for Samolet TZ rows that RT-001/002/003 still block.

Public / synthetic proxies can support Messick *content* and *substantive*
aspects for the engine. They cannot supply the *external* (criterion) aspect
that CLOSED requires. Not a new port. Does not close the three blockers.
"""

from __future__ import annotations

from typing import Any, Final

from aerobim.domain.egrz_intake_xml_checks import egrz_intake_catalog_snapshot
from aerobim.domain.npa_legal_force import overlay_egrz_intake, overlay_ids_pack

CLAIM_LEVEL: Final = "tz_proxy_rehearsal"
CLAIM_BOUNDARY: Final = (
    "Public and synthetic proxies for Task 07 rows that still need Samolet files. "
    "Messick content/substantive evidence for the engine is not criterion validity "
    "on a customer PD/RD + expertise corpus. Official MOEXP IDS is a jurisdiction "
    "profile, not a Samolet-signed EIR. IfcClash on planted or open federated IFC "
    "is not MEP system-aware delivery. Checkpoint NO_GO. "
    "closes_rt001=false, closes_rt002=false, closes_rt003=false."
)

# Messick, S. (1995). Validity of psychological assessment. American Psychologist
# 50(9), 741–749. Unified construct validity: six aspects. Used here as the
# evaluation frame for TZ accuracy / acceptance / clash claims — not as a
# psychology instrument.
MESSICK_ASPECTS: Final[tuple[str, ...]] = (
    "content",
    "substantive",
    "structural",
    "generalizability",
    "external",
    "consequential",
)


def typical_remark_taxonomy_proxy() -> dict[str, Any]:
    """Exp B coverage map vs public typical-remark catalogs (not TP/FP).

    Sources are cited, not republished. Counts are AUTHOR_CLAIM coverage
    statuses from the 2026-08-05 experiment, not product precision.
    """
    return {
        "claim_level": "coverage_map_only",
        "closes_rt001": False,
        "messick_aspect_supported": ["content"],
        "messick_aspect_missing": ["external", "generalizability"],
        "construct": (
            "RF expertise typical-remark *classes* (PP RF 87 section headings), "
            "not document-level dual-adjudicated findings on a customer package"
        ),
        "why_not_criterion_valid": (
            "PP RF 878 §23 public EGRZ fields are metadata; paired PD + "
            "expertise remarks are not an open dataset. Dual κ/α + held-out FN "
            "need that pair."
        ),
        "catalogs": [
            {
                "id": "kirov-kr",
                "organ": "Kirov state expertise",
                "pp87_section": "4",
                "discipline": "KR",
                "n": 24,
                "detectable": 4,
                "conditional": 8,
                "out_of_scope": 6,
                "not_detected": 6,
                "detectable_share": 0.167,
                "citation": (
                    "https://new.expertiza.kirov.ru/wp-content/uploads/2025/02/"
                    "Типовые-ошибки-по-разделу-4-КР-проектной-документации.pdf"
                ),
                "evidence": "docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
                "detectable_openers": [
                    "AEROBIM-PACKAGE-TECHNICAL-SPEC-MISSING-TOPIC",
                    "SECTION-PAIR-KZH",
                    "AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION",
                    "AEROBIM-PACKAGE-MISSING-SECTION",
                ],
            },
            {
                "id": "mordovia-ar-3kv2024",
                "organ": "Mordovia state expertise",
                "pp87_section": "3",
                "discipline": "AR",
                "n": 12,
                "detectable": 2,
                "conditional": 6,
                "out_of_scope": 2,
                "not_detected": 2,
                "detectable_share": 0.17,
                "citation": "https://www.xn--13-6kclkmgo9almibr3n.xn--p1ai/services/TO/3kv2024.pdf",
                "evidence": "docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
            },
            {
                "id": "mordovia-vk-3kv2024",
                "organ": "Mordovia state expertise",
                "pp87_section": "5.2-5.3",
                "discipline": "VK",
                "n": 16,
                "detectable": 4,
                "conditional": 8,
                "out_of_scope": 2,
                "not_detected": 2,
                "detectable_share": 0.25,
                "citation": "https://www.xn--13-6kclkmgo9almibr3n.xn--p1ai/services/TO/3kv2024.pdf",
                "evidence": "docs/evidence/EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md",
                "rt003_conditional_rows": 2,
            },
        ],
        "note": (
            "Kirov KR vs Mordovia AR/VK are different organs and list styles; "
            "shares are not a meta-analytic effect size."
        ),
        "egrz_intake_xml": (
            "MinStroy XSD intake pre-check is format-fail rehearsal, not a "
            "remark catalog and not dual-adjudicated TP/FP."
        ),
    }


def egrz_intake_xml_proxy() -> dict[str, Any]:
    """ECPE/EGRZ XML intake shape. Not expertise remarks. Not RT-001 CLOSED."""

    return overlay_egrz_intake(
        {
            "claim_level": "egrz_intake_precheck",
            "closes_rt001": False,
            "messick_aspect_supported": ["content", "substantive"],
            "messick_aspect_missing": ["external", "generalizability"],
            "construct": (
                "Well-formedness, declared root, and XSD 1.1 where XMLSchema11 "
                "can load the published MinStroy schema. ECPE returns packages "
                "for XML/format failures before an expert writes remarks."
            ),
            "why_not_criterion_valid": (
                "Intake format failures are not dual-adjudicated expertise "
                "remarks. PP RF 878 §23 public EGRZ fields stay metadata. "
                "PZ 01.07 / ZnP 01.01 match ECPE versions but still need a "
                "documentation xml:id strip to load; zip folders contain "
                "'dev_'; no official instance XML. Not a remark corpus."
            ),
            **egrz_intake_catalog_snapshot(),
        }
    )


def jurisdiction_ids_proxy() -> dict[str, Any]:
    """Official GAU MO IDS as ISO 19650-like information requirements — not BEP."""
    return overlay_ids_pack(
        "MOEXP-GAU-IDS",
        {
            "claim_level": "official_ids_engine_coverage",
            "closes_rt002": False,
            "customer_signed": False,
            "samolet_alias": False,
            "approval": None,
            "iso19650_role": "jurisdiction_eir_like",
            "iso19650_not": "appointing_party_eir_or_bep",
            "profile_id": "MOEXP-GAU-IDS",
            "source_page": (
                "https://www.moexp.ru/services/tekhnologii-informatsionnogo-modelirovaniya/"
            ),
            "messick_aspect_supported": ["content", "substantive", "structural"],
            "messick_aspect_missing": ["external"],
            "construct": (
                "buildingSMART IDS 1.0 executed by IfcTester against official "
                "MosoblGosExpertiza specifications. That is engine coverage of a "
                "public jurisdiction information requirement, not Samolet acceptance."
            ),
            "why_not_criterion_valid": (
                "RT-002 CLOSED needs a customer_approved pack with a full approval "
                "object and matching pack_hash. A public GAU IDS zip is not that pack."
            ),
            "ids_pack_rel": "samples/ids/moexp/pack",
            "coverage_evidence": "docs/evidence/norm-pack-moexp-coverage-2026-08.json",
        },
    )


def moscow_agr_ids_proxy() -> dict[str, Any]:
    """Official ДГП AGR IDS from stroimprosto.mos.ru — still not Samolet."""
    return overlay_ids_pack(
        "MOSCOW-AGR-DGP-IDS",
        {
            "claim_level": "official_ids_engine_coverage",
            "closes_rt002": False,
            "customer_signed": False,
            "samolet_alias": False,
            "approval": None,
            "iso19650_role": "jurisdiction_eir_like",
            "iso19650_not": "appointing_party_eir_or_bep",
            "profile_id": "MOSCOW-AGR-DGP-IDS",
            "source_page": "https://stroimprosto.mos.ru/knowledge/article/cim-agr/",
            "messick_aspect_supported": ["content", "substantive", "structural"],
            "messick_aspect_missing": ["external"],
            "construct": (
                "buildingSMART IDS executed against official Moscow AGR files "
                "(АР / БиО / ПС / МССК). City knowledge-base pack, not appointing-party EIR."
            ),
            "why_not_criterion_valid": (
                "RT-002 CLOSED needs Samolet approval + pack_hash. A public ДГП "
                "IDS zip is not that pack and is not the frozen moscow_agr DI port."
            ),
            "ids_pack_rel": "samples/ids/moscow-agr/pack",
            "coverage_evidence": "docs/evidence/norm-pack-moscow-agr-coverage-2026-08.json",
        },
    )


def spbexp_ids_proxy() -> dict[str, Any]:
    """Official SPb GAU CGE IDS 1.0 — second GAU pack, still not Samolet."""
    return overlay_ids_pack(
        "SPBEXP-GAU-CGE-IDS",
        {
            "claim_level": "official_ids_engine_coverage",
            "closes_rt002": False,
            "customer_signed": False,
            "samolet_alias": False,
            "approval": None,
            "iso19650_role": "jurisdiction_eir_like",
            "iso19650_not": "appointing_party_eir_or_bep",
            "profile_id": "SPBEXP-GAU-CGE-IDS",
            "source_page": "https://www.spbexp.ru/bim/docs/",
            "messick_aspect_supported": ["content", "substantive", "structural"],
            "messick_aspect_missing": ["external"],
            "construct": (
                "Official SPb GAU CGE IDS 1.0 (ЦИМ ОКС 3.1.0 + ЦИМ РИИ 1.1.0). "
                "Second public GAU jurisdiction pack after MOEXP."
            ),
            "why_not_criterion_valid": (
                "A second GAU pack is still not a customer_approved Samolet profile."
            ),
            "ids_pack_rel": "samples/ids/spbexp/pack",
            "coverage_evidence": "docs/evidence/norm-pack-spbexp-coverage-2026-08.json",
        },
    )


def public_jurisdiction_ids_packs() -> tuple[dict[str, Any], ...]:
    return (
        jurisdiction_ids_proxy(),
        moscow_agr_ids_proxy(),
        spbexp_ids_proxy(),
    )


def geometric_clash_proxy() -> dict[str, Any]:
    """IfcClash intersection rehearsal. Not system-aware MEP (ТР-15 / RT-003)."""
    return {
        "claim_level": "open_bench_only",
        "closes_rt003": False,
        "mep_system_clash": "NOT_VERIFIED",
        "tz_row_tr14": "geometric BIM clashes — engine rehearsal, status stays partial",
        "tz_row_tr15": "MEP system-aware clash — still not_verified (MEP-CLASH-001)",
        "messick_aspect_supported": ["content", "substantive"],
        "messick_aspect_missing": ["external", "generalizability"],
        "construct": (
            "IfcOpenShell IfcClash intersection (optional extra). Planted "
            "overlapping solids test the engine; AABB extent P/R on the n=6 "
            "fixture is a different construct (extents, not mesh)."
        ),
        "why_not_criterion_valid": (
            "No signed clearance matrix, no coordinator BCF gold, no customer "
            "federated IFC. Public IFC-Bench pairs have no clash ground truth. "
            "G55 Solibri BCF is third-party client data and must not be vendored."
        ),
        "aabb_fixture_note": (
            "docs/evidence/clash-measurement-slice-2026-08: AABB P/R=1.0 n=6 "
            "fixture_only — not IfcClash mesh, not TZ >90%"
        ),
        "planted_ifc_rel": "samples/ifc/clash-two-overlapping-boxes.ifc",
        "planted_federated_a_rel": "samples/ifc/clash-federated-box-a.ifc",
        "planted_federated_b_rel": "samples/ifc/clash-federated-box-b.ifc",
        "planted_federated_pipe_b_rel": "samples/ifc/clash-federated-pipe-b.ifc",
        "open_federated_duplex_rel": ".local/ifc-bench-v2/projects/duplex/{arc,mep}.ifc",
    }


def tz_row_proxy_map() -> dict[str, Any]:
    """Honest maximum for Task 07 rows that still need the customer."""
    return {
        "TR-8": {
            "tz": "IDS / IFC properties",
            "without_samolet": "done on fixtures + MOEXP + BSI TestCases",
            "status": "done",
            "closes_blocker": None,
        },
        "TR-11": {
            "tz": "Customer-approved norm pack",
            "without_samolet": (
                "MOEXP + Moscow AGR IDS + SPb CGE IDS jurisdiction pointers; "
                "intake template unsigned"
            ),
            "status": "partial",
            "closes_blocker": "RT-002",
        },
        "TR-14": {
            "tz": "Geometric BIM clashes (IfcClash)",
            "without_samolet": "IfcClashDetector + detect_between + planted fixture rehearsal",
            "status": "partial",
            "closes_blocker": None,
        },
        "TR-15": {
            "tz": "MEP system-aware clash",
            "without_samolet": "federated inventory AABB; IfcClash optional; still NOT_VERIFIED",
            "status": "not_verified",
            "closes_blocker": "RT-003",
        },
        "TR-6": {
            "tz": "Native DWG",
            "without_samolet": "DXF/PDF-A only; LibreDWG not linked",
            "status": "TZ_MANDATORY_UNSUPPORTED",
            "closes_blocker": None,
        },
        "accuracy_protocol": {
            "tz": "Detection accuracy after dual adjudication",
            "without_samolet": (
                "Exp B coverage map + synthetic planted defects + MinStroy "
                "XSD intake pre-check (PZ 01.07 / ZnP 01.01; xml:id sanitize)"
            ),
            "status": "blocked",
            "closes_blocker": "RT-001",
        },
    }


def construct_validity_frame() -> dict[str, Any]:
    return {
        "theory": "Messick 1995 unified construct validity (six aspects)",
        "theory_url": "https://files.eric.ed.gov/fulltext/ED380496.pdf",
        "l1_l2_l3": "docs/quality/OPEN_BENCH_VS_RT001_DECISION_2026_08_04.md",
        "aspects": {
            "content": (
                "Typical-remark taxonomy, official IDS specs, planted overlapping "
                "solids — relevance of items to the *engine* construct."
            ),
            "substantive": (
                "IfcTester / IfcClash / inventory actually run; capability errors "
                "are explicit (skipped/failed), not silent empty-as-OK."
            ),
            "structural": (
                "Scores stay typed: coverage_map_only, official_ids_engine_coverage, "
                "capability status. Do not collapse them into one F1."
            ),
            "generalizability": (
                "Open benches and GAU IDS do not generalize to Samolet PD/RD + "
                "expertise remarks (AECV-Bench §6; PP RF 878 §23)."
            ),
            "external": (
                "Criterion evidence = dual-expert TP/FP on the customer package. "
                "Absent → RT-001/002/003 stay OPEN."
            ),
            "consequential": (
                "Publishing L1/L2 as Checkpoint GO would be an invalid use of "
                "the scores (Claims Lock)."
            ),
        },
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "checkpoint": "NO_GO",
    }
