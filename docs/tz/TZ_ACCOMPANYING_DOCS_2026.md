---
title: "AeroBIM TZ Accompanying Documentation 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-19"
tags: [aerobim, tz, documentation]
---

# TZ Accompanying Documentation Checklist

Fills **«Требования к сопроводительной документации = TBD»**.

Public GitHub carries the **TechLab jury pack** only. Operator runbooks and NDA materials are local (`.local/`, `samples/customer/`).

## 1. Mandatory pack for TZ / jury review

| Document | Path | Role |
|----------|------|------|
| Jury memo (RU) | [`../docs.md`](../docs.md) | Technical justification |
| Strategy | [`../samolet.md`](../samolet.md) | Samolet wedge |
| Compliance matrix | [`TZ_COMPLIANCE_MATRIX_2026.md`](TZ_COMPLIANCE_MATRIX_2026.md) | TZ ↔ product |
| Architecture requirements | [`TZ_ARCHITECTURE_REQUIREMENTS_2026.md`](TZ_ARCHITECTURE_REQUIREMENTS_2026.md) | Architecture fill |
| Build & quality | [`TZ_BUILD_AND_QUALITY_2026.md`](TZ_BUILD_AND_QUALITY_2026.md) | Build fill |
| Solution image & presentation | [`TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md`](TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md) | Demo + slides |
| Claim boundary | [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md) | Verified vs non-claims |
| Claims lock / blockers | [`../../audit/reports/`](../../audit/reports/) | Wording + **NO_GO** |
| Samolet alignment | [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) | R1–R15 |
| Architecture SSOT | [`../architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md`](../architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md) | Hybrid target |
| Reproducibility | [`../REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md) | FAIR |
| Security | [`../../SECURITY.md`](../../SECURITY.md) | Reporting |
| Appendix manifest | [`../../samples/tz-appendix/MANIFEST.json`](../../samples/tz-appendix/MANIFEST.json) | Data appendices |
| Partners readiness | [`../partners/TECHLAB_TASK_07_READINESS_2026.md`](../partners/TECHLAB_TASK_07_READINESS_2026.md) | Form copy |

## 2. Customer-local (not on GitHub)

| Artifact | Pointer |
|----------|---------|
| NDA customer PDF/DWG pack | `samples/customer/` (gitignored) |
| Operator runbooks / Red Team dumps | `.local/engineering-docs/` |

## 3. Update discipline

When a TZ-visible capability ships:

1. Update compliance matrix status/phase.
2. Update claim boundary if newly **verified**.
3. Attach citeable evidence under `docs/evidence/` with date stamp.
4. Refresh this checklist only if a new **mandatory** jury doc class appears.
