"""Catalog of operator CLI tools (grouping; does not delete modules)."""

from __future__ import annotations

from typing import Final

# Sprint-era one-off runners — keep importable, prefer scripts/sprint-archive docs.
SPRINT_ARCHIVE_TOOLS: Final[tuple[str, ...]] = (
    "run_sprint2_synthetic_baseline",
    "run_sprint_2_1_baseline",
    "run_sprint3_open_corpus_battery",
    "run_demo_path",
)

EVALUATE_TOOLS: Final[tuple[str, ...]] = (
    "evaluate_detection_precision",
    "evaluate_drawing_advisory_grounding",
    "evaluate_extraction",
    "evaluate_ifc_qa",
    "evaluate_llm_extraction",
    "evaluate_ranking_quality",
    "evaluate_region_detection",
)

EXPORT_TOOLS: Final[tuple[str, ...]] = (
    "export_api_contract_summary",
    "export_check_coverage",
    "export_detections_from_report",
    "export_drawing_contour",
    "export_evidence_bundle",
    "export_finding_revision_delta",
    "export_gni_anonymization_pin",
    "export_hybrid_route_matrix",
    "export_ids_fail_closed_gate",
    "export_ifc_release_matrix",
    "export_moexp_ids_coverage",
    "export_public_ids_pack_coverage",
    "export_release_attestation",
    "export_runtime_baseline",
    "export_samples_manifest",
    "export_solihin_rule_classes",
    "export_sprint2_dataset_manifest",
    "export_stale_norm_scan",
    "export_weekly_eng_status",
)

CORE_OPERATOR_TOOLS: Final[tuple[str, ...]] = (
    "benchmark_project_package",
    "run_vertical_slice",
    "run_demo_vertical_slice",
    "validate_dwg_toolchain",
    "verify_bcf_t2_evidence",
    "verify_bcf_structural_handoff",
    "verify_kt2_handoff",
    "verify_evidence_bundle",
    "verify_release_evidence",
    "compose_advisory_remark",
    "validate_customer_intake_gate",
    "measure_package_sla",
    "offline_bundle",
    "seed_smoke_report",
)


def catalog() -> dict[str, tuple[str, ...]]:
    return {
        "core": CORE_OPERATOR_TOOLS,
        "evaluate": EVALUATE_TOOLS,
        "export": EXPORT_TOOLS,
        "sprint_archive": SPRINT_ARCHIVE_TOOLS,
    }


def active_tools() -> tuple[str, ...]:
    """Operator-facing tools kept in the active catalog (≤40)."""

    return CORE_OPERATOR_TOOLS + EVALUATE_TOOLS + EXPORT_TOOLS
