"""Static honesty surface for product capabilities (not runtime probe results)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aerobim.domain.calculation_evidence import (
    CALCULATION_CORRECTNESS_CLAIM,
    CALCULATION_CORRECTNESS_REASON,
)
from aerobim.domain.capability_contract import capability_contract
from aerobim.domain.errors import HonestyCapabilityError
from aerobim.domain.mep_intake import assess_mep_customer_intake
from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

_MEP_ALLOWED = frozenset(
    {
        CapabilityState.NOT_VERIFIED,
        CapabilityState.MISSING,
        CapabilityState.FAILED,
    }
)
_DWG_DXF_ALLOWED = frozenset(
    {
        CapabilityState.MISSING,
        CapabilityState.FAILED,
        CapabilityState.NOT_VERIFIED,
        CapabilityState.SKIPPED,
    }
)
_CALC_CORRECTNESS_ALLOWED = frozenset(
    {
        CapabilityState.NOT_IMPLEMENTED,
        CapabilityState.MISSING,
        CapabilityState.FAILED,
    }
)


def default_honesty_capabilities() -> ReportCapabilities:
    """Policy defaults: gaps stay MISSING / NOT_VERIFIED / NOT_IMPLEMENTED."""

    return ReportCapabilities()


def _repo_root_candidates() -> list[Path]:
    return [
        Path(__file__).resolve().parents[4],
        Path.cwd(),
    ]


def load_customer_intake_gate_snapshot() -> dict[str, Any]:
    """Best-effort load of audit/evidence/customer-intake-gate.json for honesty API."""

    for root in _repo_root_candidates():
        path = root / "audit" / "evidence" / "customer-intake-gate.json"
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        gates = payload.get("gates") if isinstance(payload, dict) else None
        true_gates = (
            [key for key, value in gates.items() if value is True]
            if isinstance(gates, dict)
            else []
        )
        return {
            "status": payload.get("status", "UNKNOWN"),
            "claim_level": payload.get("claim_level", "unknown"),
            "true_gates": true_gates,
            "checkpoint": "NO_GO",
            "source": "audit/evidence/customer-intake-gate.json",
        }
    return {
        "status": "MISSING_GATE_FILE",
        "claim_level": "not_ready",
        "true_gates": [],
        "checkpoint": "NO_GO",
        "source": None,
    }


def load_bcf_t2_status_snapshot() -> dict[str, Any]:
    """Load T2 CDE import proof STATUS.json — never invent VERIFIED."""

    for root in _repo_root_candidates():
        path = root / "audit" / "evidence" / "cde-import-proof" / "STATUS.json"
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("status") or "NOT_VERIFIED")
        present = payload.get("present_files") or []
        required = payload.get("required_files") or [
            "import-log.txt",
            "screenshot.png",
            "hashes.json",
        ]
        claim_allowed = bool(payload.get("claim_allowed")) and status == "VERIFIED"
        return {
            "status": "not_verified" if status != "VERIFIED" else "available",
            "ladder_tier": "T2",
            "raw_status": status,
            "claim_allowed": claim_allowed,
            "required_files": required,
            "present_files": present,
            "source": "audit/evidence/cde-import-proof/STATUS.json",
            "reason": (
                "customer CDE import environment is not provided"
                if not present
                else f"T2 status={status}"
            ),
        }
    return {
        "status": "not_verified",
        "ladder_tier": "T2",
        "raw_status": "MISSING_STATUS_FILE",
        "claim_allowed": False,
        "required_files": ["import-log.txt", "screenshot.png", "hashes.json"],
        "present_files": [],
        "source": None,
        "reason": "customer CDE import environment is not provided",
    }


def load_mep_intake_snapshot() -> dict[str, object]:
    """Default MEP intake without customer scope — blocked_customer_data."""

    result = assess_mep_customer_intake(
        None,
        matrix_path_exists=False,
        matrix_synthetic=True,
    )
    payload = result.as_dict()
    payload["rt_003"] = "OPEN"
    payload["gap_id"] = "MEP-CLASH-001"
    return payload


def build_auth_bff_capability() -> dict[str, object]:
    """Honesty surface for production OIDC BFF — designed, not implemented."""

    return {
        "status": "NOT_IMPLEMENTED",
        "design": "docs/architecture/POST05_OIDC_BFF_DESIGN_2026_07.md",
        "dev_proxy": "Vite loopback Authorization inject only",
        "phase_2_stubs": "login/callback/logout with CSRF state (no production session)",
        "phase_2_5_pkce": (
            "S256 code_challenge on login; optional IdP authorize URL draft via "
            "AEROBIM_OIDC_BFF_CLIENT_ID + AEROBIM_OIDC_BFF_AUTHORIZE_URL — still 501"
        ),
        "phase_3_pending": "HttpOnly session cookie + IdP code exchange + FE bearer removal",
        "phase_3_lab": (
            "Code-landed behind oidc_bff_phase3_ready (token URL + client secret + "
            "cookie secret + redirect allowlist). Default remains NOT_IMPLEMENTED."
        ),
    }


def build_four_direction_contracts() -> list[dict[str, Any]]:
    """Unified honesty contracts for DWG / MEP / calc / BCF→СОД."""

    t2 = load_bcf_t2_status_snapshot()
    return [
        capability_contract(
            capability="native_dwg",
            status="missing",
            evidence_level="unit",
            affects_pass=True,
            reason="native DWG parser is not implemented",
            claim_boundary=(
                "DWG via conversion or licensed adapter only — never dwg_supported / DWG-ready"
            ),
            dependencies=["CadModelIngestor"],
            evidence_refs=[
                "STUB-ODA-CAD-001",
                "docs/pilot/FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md",
            ],
        ),
        capability_contract(
            capability="dxf_ingest",
            status="partial",
            evidence_level="fixture",
            affects_pass=True,
            reason="DXF TEXT/MTEXT via optional ezdxf; dwg_dxf never OK",
            claim_boundary="DXF partial ≠ native DWG support",
            dependencies=["aerobim-backend[cad]", "ezdxf"],
            evidence_refs=["samples/cad/minimal-entities.dxf"],
        ),
        capability_contract(
            capability="dwg_derived_pdf_ifc_route",
            status="partial",
            evidence_level="unit",
            affects_pass=True,
            reason=(
                "PDF/IFC/DXF may be used as derived inputs with provenance — "
                "available_as_derived_input, not dwg_supported"
            ),
            claim_boundary="Conversion is an external prep step, not DWG support",
            dependencies=["DerivedCadProvenance"],
            evidence_refs=["backend/src/aerobim/domain/cad_ingest.py"],
        ),
        capability_contract(
            capability="geometric_clash",
            status="partial",
            evidence_level="fixture",
            affects_pass=True,
            reason="Hard IFC clash via optional ifcclash when configured",
            claim_boundary="Geometric hard clash ≠ full MEP system-aware clash",
            dependencies=["IfcClashDetector"],
            evidence_refs=["docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md"],
        ),
        capability_contract(
            capability="mep_system_graph",
            status="fixture_only",
            evidence_level="fixture",
            affects_pass=True,
            reason="Co-presence / ENG_FIXTURE graph scaffold — not customer connectivity",
            claim_boundary="Co-presence is not connection proof",
            dependencies=["MepSystemGraphProvider", "RT-003"],
            evidence_refs=["MEP-CLASH-001"],
        ),
        capability_contract(
            capability="mep_system_aware_rules",
            status="blocked_customer_data",
            evidence_level="unit",
            affects_pass=True,
            reason="federated MEP model and customer rules are required",
            claim_boundary="RT-003 OPEN — full MEP system-aware not available",
            dependencies=["federated IFC", "signed clearance matrix", "scope memo"],
            evidence_refs=["MEP-CLASH-001", "samples/mep/clearance-matrix.schema.json"],
        ),
        capability_contract(
            capability="mep_clearance_validation",
            status="fixture_only",
            evidence_level="fixture",
            affects_pass=True,
            reason="Template matrix + geometry_verified=False on analyze path",
            claim_boundary="Template clearance ≠ customer-validated clearance",
            dependencies=["clearance matrix"],
            evidence_refs=["samples/mep/clearance-matrix-template.json"],
        ),
        capability_contract(
            capability="mep_service_zone_validation",
            status="not_implemented",
            evidence_level="unit",
            affects_pass=True,
            reason="Service / maintenance envelope checks not implemented",
            claim_boundary="Roadmap after RT-003",
            evidence_refs=["docs/roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md"],
        ),
        capability_contract(
            capability="calculation_match",
            status="partial",
            evidence_level="fixture",
            affects_pass=True,
            reason="evidence_consistency_only — load/qty/cross-doc/OpenRebar сверка",
            claim_boundary=("сверка переданных результатов и источников, не расчётный решатель"),
            dependencies=[
                "LoadEvidenceVerifier",
                "QuantityConsistencyChecker",
                "ExternalEvidenceVerifier",
            ],
            evidence_refs=["domain/calculation_evidence.py"],
        ),
        capability_contract(
            capability="calculation_correctness",
            status="not_implemented",
            evidence_level="unit",
            affects_pass=True,
            reason=CALCULATION_CORRECTNESS_REASON,
            claim_boundary=CALCULATION_CORRECTNESS_CLAIM,
            evidence_refs=["ReportCapabilities.calculation_correctness"],
        ),
        capability_contract(
            capability="bcf_21_export",
            status="available",
            evidence_level="integration",
            affects_pass=False,
            reason="BCF 2.1 ZIP export AVAILABLE (T0)",
            claim_boundary="Export ≠ CDE import",
            evidence_refs=["audit/evidence/bcf-structural-handoff-2026-07-25.json"],
        ),
        capability_contract(
            capability="bcf_t1_structural",
            status="available",
            evidence_level="integration",
            affects_pass=False,
            reason="T1 structural handoff evidenced",
            claim_boundary="Structural ZIP ≠ CDE interoperable",
            evidence_refs=["docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md"],
        ),
        capability_contract(
            capability="bcf_cde_t2_import",
            status="not_verified",
            evidence_level="unit",
            affects_pass=True,
            reason=str(t2.get("reason") or "customer CDE import environment is not provided"),
            claim_boundary=(
                "T2 requires import-log + screenshot + hashes — never CDE_READY without them"
            ),
            dependencies=["customer CDE sandbox"],
            evidence_refs=["audit/evidence/cde-import-proof/STATUS.json"],
        ),
    ]


def build_system_capabilities_payload() -> dict[str, object]:
    caps = default_honesty_capabilities()
    honesty = {
        "dwg_dxf": asdict(caps.dwg_dxf),
        "cv_human_level": asdict(caps.cv_human_level),
        "mep_system_clash": asdict(caps.mep_system_clash),
        "calculation_match": asdict(caps.calculation_match),
        "calculation_correctness": asdict(caps.calculation_correctness),
    }
    intake = load_customer_intake_gate_snapshot()
    auth_bff = build_auth_bff_capability()
    t2 = load_bcf_t2_status_snapshot()
    mep_intake = load_mep_intake_snapshot()
    directions = build_four_direction_contracts()
    return {
        "artifact_type": "system_capabilities",
        "schema_version": "1.3.0",
        "claim_boundary": {
            "calculation_match": (
                "сверка результатов (numeric/provenance match) — PARTIAL when evaluated"
            ),
            "calculation_correctness": (
                "независимая проверка корректности расчёта — НЕ РЕАЛИЗОВАНО "
                f"({CALCULATION_CORRECTNESS_CLAIM})"
            ),
            "dwg_dxf": (
                "native DWG MISSING; DXF PARTIAL via optional ezdxf; "
                "ODA stub STUB-ODA-CAD-001 not on analyze path — never OK; "
                "PDF/IFC = derived input route only"
            ),
            "cv_human_level": (
                "HybridDrawingAnalyzer priors+OCR (vision extra optional); "
                "no YOLO weights; AECV-Bench symbol counting unsolved — MISSING"
            ),
            "mep_system_clash": (
                "Hard geometric clash separate; MEP graph fixture_only / "
                "blocked_customer_data until RT-003 — MEP-CLASH-001 NOT VERIFIED"
            ),
            "precision_claim": (
                "Publishable only with customer corpus + ≥2 adjudicators + κ/α "
                "agreement + held-out split + FN tracked (never synthetic-only)"
            ),
            "customer_sla": (
                "Fixture SLA ≠ customer комплект SLA; customer_measurable requires "
                "corpus_kind=customer + pack_hash + machine_fingerprint + "
                "mandatory_capabilities_complete (schema 1.3.0)"
            ),
            "ifc_knowledge_graph": (
                "I9 advisory scaffold: relational fixture QA + stub fallback — "
                "not GraphRAG / IfcLLM product"
            ),
            "auth_bff": (
                "Production Authorization Code + PKCE BFF with HttpOnly session cookie — "
                "DESIGNED / NOT_IMPLEMENTED (POST-05); Vite loopback inject is dev-only"
            ),
            "bcf_cde": (
                "BCF ZIP structural AVAILABLE (T0/T1); CDE import NOT_VERIFIED (T2) — "
                "docs/architecture/BCF_EVIDENCE_LADDER_T0_T4_2026_07.md"
            ),
            "llm_advisory": (
                "Advisory-only hybrid contour; cannot set summary.passed / outcome; "
                "customer data default deny; cloud policy often CLOUD_DATA_POLICY_UNKNOWN"
            ),
        },
        "honesty": honesty,
        "direction_contracts": directions,
        "bcf_t2": t2,
        "mep_intake": mep_intake,
        "auth_bff": auth_bff,
        "customer_intake_gate": intake,
        "llm_advisory": {
            "status": "skipped",
            "advisory_only": True,
            "affects_summary_passed": False,
            "customer_data_default": "deny",
            "providers_mock_tested": ["kimi", "qwen", "gemma"],
            "local_profile": "private_qwen_local",
            "studio_profile": "private_yandex_ai_studio",
            "cloud_max_status": "NOT_VERIFIED",
            "requires_model_revision": True,
            "token_budget_scope": "process_local_or_file_shared",
            "token_budget_note": (
                "Day counters are process-local unless AEROBIM_LLM_BUDGET_LEDGER is set; "
                "N workers without a ledger ≈ N× daily cap (RT-BUDGET-03). "
                "File ledger: stale .lock cleared by mtime; lock timeout sets "
                "lock_degraded=true in usage (RT-LEDGER-01). "
                "TOCTOU overshoot ≤ N×max_tokens_per_call between check and record "
                "(RT-LEDGER-02; documented, not reserved)."
            ),
            "pii_gate": {
                "active": True,
                "effectiveness_on_customer_sheets": "NOT_MEASURED",
                "claim_boundary": ("PII gate active; effectiveness on real sheets not measured"),
                "exclusion_counters": [
                    "excluded_by_role",
                    "excluded_by_geometry",
                    "excluded_unknown_role",
                ],
            },
            "claim_boundary": (
                "OpenAI-compat advisory (vLLM local or Yandex AI Studio RF) when "
                "AEROBIM_LLM_ADVISORY_ENABLED (+ deprecated LOCAL alias until 2026-09-21) "
                "+ AEROBIM_LLM_MODEL_REVISION or unversioned gpt:// pin; token caps "
                "fail-closed; Alibaba Max NOT_VERIFIED; Studio cloud = PUBLIC/INTERNAL "
                "only; never sets summary.passed; ai_generated drafts require expert "
                "confirmation; HTTP remark.content_marking + BCF provenance/label "
                "carry ai_generated=true;expert_confirmation_required=true; "
                "unavailable model → SKIPPED not FAILED; not product accuracy; "
                "model never sets severity (deterministic policy owns it)"
            ),
            "remark_shape": {
                "title": "example",
                "body": "example",
                "ai_generated": True,
                "expert_confirmation_required": True,
                "content_marking": "ai_generated=true;expert_confirmation_required=true",
                "claim_boundary": "advisory draft; expert confirmation required",
                "provider": None,
                "model": None,
                "prompt_version": None,
                "evidence_refs": [],
            },
            "content_marking_egress": {
                "http_remark_field": "remark.ai_generated + remark.content_marking",
                "bcf_description_provenance": (
                    "ai_generated=true;expert_confirmation_required=true"
                ),
                "bcf_label": "ai_generated:true",
            },
        },
        "forbidden_ok_states": {
            "dwg_dxf": [CapabilityState.OK.value],
            "cv_human_level": [CapabilityState.OK.value],
            "mep_system_clash": [CapabilityState.OK.value],
            "calculation_correctness": [CapabilityState.OK.value],
        },
        "forbidden_claim_phrases": [
            "DWG поддерживается",
            "DWG-ready",
            "dwg_supported",
            "полный MEP clash",
            "проверка корректности расчётов",
            "calculation_correctness_verified",
            "independent calculation correctness verified",
            "solver verification passed",
            "расчётная корректность подтверждена",
            "BCF готов для СОД",
            "CDE interoperable",
            "CDE_READY",
        ],
        "notes": [
            (
                "Runtime report.capabilities may flip evaluated contours "
                "(clash/ids/raster/dxf) to ok/failed/skipped/not_verified."
            ),
            (
                "Honesty fields above must not silently become ok without "
                "an explicit product delivery change."
            ),
            "Checkpoint remains NO_GO until RT-001/002/003 customer evidence.",
            (
                "auth_bff remains NOT_IMPLEMENTED until POST-05 phases 2–3 ship; "
                "see docs/architecture/POST05_OIDC_BFF_DESIGN_2026_07.md."
            ),
            (
                "direction_contracts use unified status vocabulary; "
                "fixture_only ≠ customer; not_verified ≠ available."
            ),
        ],
    }


def enforce_honesty_capabilities(capabilities: ReportCapabilities) -> None:
    """Runtime fail-closed: declared gaps must not look delivered."""

    checks: tuple[tuple[str, CapabilityStatus, frozenset[CapabilityState]], ...] = (
        ("dwg_dxf", capabilities.dwg_dxf, _DWG_DXF_ALLOWED),
        (
            "cv_human_level",
            capabilities.cv_human_level,
            frozenset({CapabilityState.MISSING, CapabilityState.FAILED}),
        ),
        ("mep_system_clash", capabilities.mep_system_clash, _MEP_ALLOWED),
        (
            "calculation_correctness",
            capabilities.calculation_correctness,
            _CALC_CORRECTNESS_ALLOWED,
        ),
    )
    for name, status, allowed in checks:
        if status.status not in allowed:
            raise HonestyCapabilityError(
                name,
                status.status.value,
                tuple(sorted(s.value for s in allowed)),
            )


def assert_honesty_capabilities_not_silently_ok(capabilities: ReportCapabilities) -> None:
    """Architecture guard for tests — wraps ``enforce_honesty_capabilities``."""

    try:
        enforce_honesty_capabilities(capabilities)
    except HonestyCapabilityError as exc:
        raise AssertionError(str(exc)) from exc


__all__ = [
    "assert_honesty_capabilities_not_silently_ok",
    "build_auth_bff_capability",
    "build_four_direction_contracts",
    "build_system_capabilities_payload",
    "default_honesty_capabilities",
    "enforce_honesty_capabilities",
    "load_bcf_t2_status_snapshot",
    "load_customer_intake_gate_snapshot",
    "load_mep_intake_snapshot",
]
