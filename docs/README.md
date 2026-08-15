---
title: "AeroBIM Documentation — TechLab jury surface"
status: active
version: "3.3.0"
last_updated: "2026-08-14"
tags: [aerobim, documentation, samolet, techlab, jury]
claim_boundary: "Public GitHub = TechLab jury pack only. Checkpoint NO_GO. Eng readiness ≠ customer GO. Operator/debug docs are local (.local/)."
---

# Documentation (TechLab jury)

Checkpoint: **`NO_GO`** — [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md).  
Aug 2026 eng readiness: [`ENGINEERING_STATUS_2026_08.md`](ENGINEERING_STATUS_2026_08.md) (not Checkpoint GO).  
P0 eng package WP-01…08 Red Team rollup: [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md).

Public GitHub carries **only** materials needed for Samolet TechLab Task 07 jury review: product code, TZ pack, honest claims, architecture, citeable fixtures, and curated eng/Red Team summaries under `docs/quality/`. Operator runbooks, phase Red Team dumps, MicroPhoenix archive, team-private dumps (TZ/PPTX/photos), and commercial contact pipelines live under `.local/` (not published). Public `docs/customer-discovery/` = anonymized templates only.

**Red Team / eng remediations through 2026-08-02:** Claims Lock / blockers / ADR-001 / SECURITY aligned with fail-closed Shared-gate; P0 WP-01…08 eng-delivered under Claims Lock. Customer blockers RT-001/002/003 remain open.

## Read first

| File | Role |
|------|------|
| [`ENGINEERING_STATUS_2026_08.md`](ENGINEERING_STATUS_2026_08.md) | **Aug 2026 eng status** (P0 WP-01…08 + LIC-001 / P2 / offline) |
| [`quality/RED_TEAM_P0_ROLLUP_2026_08_02.md`](quality/RED_TEAM_P0_ROLLUP_2026_08_02.md) | P0 Red Team rollup (self; Checkpoint NO_GO) |
| [`docs.md`](docs.md) | **Jury memo (RU)** |
| [`samolet.md`](samolet.md) | Strategy × Samolet 10D (июль 2026) |
| [`gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md`](gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md) | **OSINT 14.08 + вектор** (Renga/Tangl/10D, монетизация) |
| [`tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md`](tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md) | Customer TZ v2.0 |
| [`tz/README.md`](tz/README.md) | Full TZ pack index |
| [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md) | Verified vs planned |
| [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) | Forbidden wording |
| [`../audit/reports/CLAIMS_LOCK_2026_07_31.md`](../audit/reports/CLAIMS_LOCK_2026_07_31.md) | Eng freeze 2026-07-31 |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | RT-001/002/003 |
| [`architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Architecture |
| [`architecture/ADR-001-verdict-ownership-2026.md`](architecture/ADR-001-verdict-ownership-2026.md) | Who owns `summary.passed` |
| [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) | R1–R15 |
| [`partners/TECHLAB_TASK_07_READINESS_2026.md`](partners/TECHLAB_TASK_07_READINESS_2026.md) | Readiness / form |
| [`roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md`](roadmap/MEP_SYSTEM_CLASH_GAP_2026_07.md) | MEP honesty |
| [`roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md`](roadmap/P2_02_GEOMETRY_HONESTY_PLAN_2026_08.md) | Geometry honesty deepen |
| [`license-policy-2026.md`](license-policy-2026.md) | LIC-001 Option B |
| [`offline-deployment-2026.md`](offline-deployment-2026.md) | Docker offline; bare-metal deferred |
| [`pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md`](pilot/QUALITY_MEASUREMENT_PROTOCOL_2026_08.md) | WP-07 quality measurement protocol |
| [`../samples/benchmarks/open-corpora/README.md`](../samples/benchmarks/open-corpora/README.md) | WP-06 open corpora profiles |

## Supporting (still jury-facing)

| File | Role |
|------|------|
| [`partners/TECHLAB_SAMOLET_APPLICATION_2026.md`](partners/TECHLAB_SAMOLET_APPLICATION_2026.md) | Application blurb |
| [`partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md`](partners/AEROBIM_STRATEGIC_ASSESSMENT_2026_07.md) | Positioning |
| [`partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md) | Ask to Samolet (RU; stack-aware 14.08) |
| [`partners/COMPETITIVE_MATRIX_2026_08.md`](partners/COMPETITIVE_MATRIX_2026_08.md) | Competitive axes + RU developers |
| [`../audit/reports/TZ_RUNTIME_MATRIX.md`](../audit/reports/TZ_RUNTIME_MATRIX.md) | Runtime capabilities |
| [`../audit/reports/CLAIMS_EVIDENCE_MATRIX.md`](../audit/reports/CLAIMS_EVIDENCE_MATRIX.md) | Claims ↔ evidence |
| [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md) | FAIR / how to reproduce |
| [`ifc-compatibility-matrix.md`](ifc-compatibility-matrix.md) | IFC schema support |
| [`evidence/README.md`](evidence/README.md) | Citeable fixtures |
| [`../audit/reports/README.md`](../audit/reports/README.md) | Public audit index |
| [`PROJECT_STATUS_AUDIT_2026.md`](PROJECT_STATUS_AUDIT_2026.md) | Self-audit / gates |
| [`capability-claim-matrix-2026.md`](capability-claim-matrix-2026.md) | Claims ↔ evidence |
| [`benchmark-evidence-2026.md`](benchmark-evidence-2026.md) | Fixture metric boundaries |
| [`pilot-protocol-samolet-2026.md`](pilot-protocol-samolet-2026.md) | Samolet pilot phases |
| [`pilot/AI_WORK_PLAN_2026_08_14.md`](pilot/AI_WORK_PLAN_2026_08_14.md) | План работ 14.08 (код freeze) + исполнение |
| [`demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md`](demo/KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md) | Скрипт видео 3 мин (человек 19.08) |
| [`partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md`](partners/SAMOLET_RENGA_IFC_REQUEST_2026_08_14.md) | Письмо: IFC из Renga, не Tangl API |
| [`pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`](pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md) | Parallel plan → Aug / Sep checkpoints |
| [`pilot/EXPERT_LABELING_INSTRUCTION_2026.md`](pilot/EXPERT_LABELING_INSTRUCTION_2026.md) | Dual-blind TP/FP/FN + κ |
| [`pilot/NORM_PACK_RASE_GUIDE_2026.md`](pilot/NORM_PACK_RASE_GUIDE_2026.md) | Norm pack + RASE |
| [`pilot/HARNESS_AND_DEMO_RUNBOOK_2026.md`](pilot/HARNESS_AND_DEMO_RUNBOOK_2026.md) | Demo evidence + precision harness |
| [`pilot/FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md`](pilot/FOUR_DIRECTION_GAP_ANALYSIS_2026_07_24.md) | DWG / MEP / calc / BCF→СОД gap + priority |
| [`../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md`](../audit/reports/HYBRID_AI_FINAL_REPORT_2026_07_28.md) | Hybrid AI design report; WP-02 advisory pre-gate landed after report |
| [`quality/RED_TEAM_WP01_03_2026_08_02.md`](quality/RED_TEAM_WP01_03_2026_08_02.md) | Red Team WP-01..03 |
| [`quality/RED_TEAM_WP04_05_2026_08_02.md`](quality/RED_TEAM_WP04_05_2026_08_02.md) | Red Team WP-04/05 |
| [`quality/RED_TEAM_WP06_08_2026_08_02.md`](quality/RED_TEAM_WP06_08_2026_08_02.md) | Red Team WP-06..08 |
| [`quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md`](quality/RED_TEAM_WAVE2_TRACKER_COMMERCIAL_2026_08_04.md) | Red Team wave-2: tracker К0 + commercial hygiene |
| [`TIER0_INDEX.md`](TIER0_INDEX.md) | Compact map |
| [`ai-safety-and-document-ingestion-2026.md`](ai-safety-and-document-ingestion-2026.md) | Trust boundaries / AI safety |
