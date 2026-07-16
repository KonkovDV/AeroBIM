---
title: "AeroBIM TZ Accompanying Documentation 2026"
status: active
version: "1.0.0"
last_updated: "2026-07-10"
tags: [aerobim, tz, documentation]
---

# TZ Accompanying Documentation Checklist

Fills **«Требования к сопроводительной документации = TBD»**.

## 1. Mandatory pack for TZ / pilot submission

| Document | Path | Role |
|----------|------|------|
| Compliance matrix | [`TZ_COMPLIANCE_MATRIX_2026.md`](TZ_COMPLIANCE_MATRIX_2026.md) | TZ ↔ product traceability |
| Architecture requirements | [`TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](TZ_ARCHITECTURE_REQUIREMENTS_2026.md) | TBD architecture fill |
| Build & quality | [`TZ_BUILD_AND_QUALITY_2026.md`](TZ_BUILD_AND_QUALITY_2026.md) | TBD build fill |
| Solution image & presentation | [`TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`](TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md) | Demo + slides |
| Claim boundary | [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md) | Verified vs non-claims |
| KPI protocol | [`../pilot-kpi-protocol-2026.md`](../pilot-kpi-protocol-2026.md) | Measurement rules |
| Samolet alignment | [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) | R1–R15 |
| Intake checklist | [`../samolet-pilot-intake-checklist-2026.md`](../samolet-pilot-intake-checklist-2026.md) | Week-1 data |
| Adjudication template | [`../samolet-kpi-adjudication-template-2026.md`](../samolet-kpi-adjudication-template-2026.md) | TP/FP log |
| Reproducibility | [`../REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md) | FAIR/CODE |
| Security | [`../../SECURITY.md`](../../SECURITY.md) | Reporting + hardening |
| Ops runbook | [`../../ops/standalone-runbook.md`](../../ops/standalone-runbook.md) | Bootstrap |
| Environment matrix | [`../../ops/environment-matrix.md`](../../ops/environment-matrix.md) | Env contract |
| Annotation / IAA | [`../annotation-protocol-2026.md`](../annotation-protocol-2026.md) | Corpus quality |
| Ablation table | [`../evidence/ablation-study-paper-table-2026.md`](../evidence/ablation-study-paper-table-2026.md) | Multimodal evidence |
| Appendix manifest | [`../../samples/tz-appendix/MANIFEST.json`](../../samples/tz-appendix/MANIFEST.json) | Data appendices |

## 2. Optional / customer-local (often gitignored)

| Artifact | Pointer |
|----------|---------|
| NDA customer PDF/DWG pack | [`../LOCAL_OPERATOR_ARTIFACTS.md`](../LOCAL_OPERATOR_ARTIFACTS.md) |
| CDE BCF roundtrip evidence | [`../pilot-cde-handoff-2026.md`](../pilot-cde-handoff-2026.md) |
| Filled IAA worksheets | `samples/benchmarks/annotation/` |
| Live review screenshots | `frontend/artifacts/` (local) |

## 3. Update discipline

When a TZ-visible capability ships:

1. Update compliance matrix status/phase.
2. Update claim boundary if newly **verified**.
3. Attach evidence under `docs/evidence/` with date stamp.
4. Refresh this checklist only if a new **mandatory** doc class appears.

## 4. Language

One language per file. Product UI strings may be RU or EN per [`../LANGUAGE-POLICY-2026.md`](../LANGUAGE-POLICY-2026.md); do not mix runglish in a single doc.
