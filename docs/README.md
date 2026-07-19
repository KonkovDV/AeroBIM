---
title: "AeroBIM Documentation Map — public GitHub surface"
status: active
version: "2.0.0"
last_updated: "2026-07-19"
tags: [aerobim, documentation, samolet, tz]
claim_boundary: "Public docs only. Operator Red Team deltas live under .local/ (gitignored)."
---

# AeroBIM documentation (public)

Checkpoint: **`NO_GO`** until RT-001/002/003 — [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md).

This index is the **only** public documentation router. Engineering wave logs, Red Team phase reports, and AI prompts are **not** on GitHub ([`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md) · [`LOCAL_OPERATOR_ARTIFACTS.md`](LOCAL_OPERATOR_ARTIFACTS.md)).

## Start here

| File | Role |
|------|------|
| [`TIER0_INDEX.md`](TIER0_INDEX.md) | Compact SSOT map |
| [`docs.md`](docs.md) | **Jury memo (RU)** — TechLab Task 07 technical justification |
| [`samolet.md`](samolet.md) | **Strategy deep dive** — why AeroBIM fits Samolet 10D |
| [`tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Customer TZ v2.0 |
| [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Verified vs planned |
| [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) | Forbidden wording |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 |
| [`architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Architecture SSOT |
| [`architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Who owns `summary.passed` |
| [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) | R1–R15 traceability |
| [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md) | FAIR / evidence |

## TZ pack

| File | Role |
|------|------|
| [`tz/README.md`](tz/README.md) | Pack index |
| [`tz/TZ_COMPLIANCE_MATRIX_2026.md`](tz/TZ_COMPLIANCE_MATRIX_2026.md) | Requirement mapping |
| [`tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md) | Architecture fill |
| [`tz/TZ_BUILD_AND_QUALITY_2026.md`](tz/TZ_BUILD_AND_QUALITY_2026.md) | Build / quality |
| [`tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`](tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md) | Demo / presentation |
| [`tz/TZ_ACCOMPANYING_DOCS_2026.md`](tz/TZ_ACCOMPANYING_DOCS_2026.md) | Accompanying checklist |
| [`../audit/reports/TZ_RUNTIME_MATRIX.md`](../audit/reports/TZ_RUNTIME_MATRIX.md) | Runtime capabilities |
| [`../audit/reports/CLAIMS_EVIDENCE_MATRIX.md`](../audit/reports/CLAIMS_EVIDENCE_MATRIX.md) | Claims ↔ evidence |

## Partners / pilot

| File | Role |
|------|------|
| [`partners/TECHLAB_TASK_07_READINESS_2026.md`](partners/TECHLAB_TASK_07_READINESS_2026.md) | Readiness + form copy |
| [`partners/TECHLAB_SAMOLET_APPLICATION_2026.md`](partners/TECHLAB_SAMOLET_APPLICATION_2026.md) | Application blurb |
| [`partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md`](partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md) | Positioning |
| [`partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) | Ask to Samolet (RU) |
| [`partners/SAMOLET_WHAT_WE_NEED_2026_07.md`](partners/SAMOLET_WHAT_WE_NEED_2026_07.md) | Ask to Samolet (EN) |
| [`samolet-pilot-intake-checklist-2026.md`](samolet-pilot-intake-checklist-2026.md) | Week-1 intake |
| [`pilot-start-package-2026.md`](pilot-start-package-2026.md) | Kickoff |
| [`pilot-kpi-protocol-2026.md`](pilot-kpi-protocol-2026.md) | KPI protocol |
| [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md) | BCF / CDE |
| [`roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) | MEP honesty |

## Architecture & reference

| File | Role |
|------|------|
| [`architecture/PHASE3_NORM_CROSSDOC_2026.md`](architecture/PHASE3_NORM_CROSSDOC_2026.md) | Norm packs / cross-doc |
| [`architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md`](architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md) | Literature posture |
| [`ifc-compatibility-matrix.md`](ifc-compatibility-matrix.md) | IFC2x3 / IFC4 / IFC4x3 |
| [`12-openrebar-provenance-decision-table.md`](12-openrebar-provenance-decision-table.md) | OpenRebar сверка |
| [`15-local-quality-gate.md`](15-local-quality-gate.md) | Local CI-equivalent gate |
| [`contributor-git-2026.md`](contributor-git-2026.md) | Safe git contrib |

## Evidence

| Path | Role |
|------|------|
| [`evidence/README.md`](evidence/README.md) | Evidence index |
| [`evidence/DOCS_SAMOLET_MATRIX_RECONCILIATION_2026_07_19.md`](evidence/DOCS_SAMOLET_MATRIX_RECONCILIATION_2026_07_19.md) | docs.md §3.1 ↔ code |
| [`../audit/evidence/`](../audit/evidence/) | BCF T1, SLA honesty, CDE STATUS |
| [`../audit/reports/README.md`](../audit/reports/README.md) | Public audit reports only |

## Historical (not first read)

| Path | Role |
|------|------|
| [`archive/`](archive/) | MicroPhoenix / rebaseline snapshots |

## Not on public GitHub

| Path | Reason |
|------|--------|
| `.local/engineering-docs/` | Red Team phase reports, deep audits |
| `docs/prompts/` | AI session prompts |
| `docs/evidence/internal/` | NDA customer evidence |
| `samples/customer/` | Customer packs (README only) |
