---
title: "Evidence Directory Index"
status: active
version: "1.1.0"
last_updated: "2026-07-17"
---

# Evidence directory

Dated, citeable verification snapshots for reviewers and pilot gates. Policy: [`../REPOSITORY-HYGIENE-2026.md`](../REPOSITORY-HYGIENE-2026.md).  
**Claims SSOT:** [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md).

## Academic honesty packs (July 2026 — prefer these)

Primary evidence now lives under [`../../audit/evidence/`](../../audit/evidence/):

| File | Role |
|------|------|
| `../../audit/evidence/audit-baseline.json` | Measured freeze (tests, LOC, optional deps) |
| `../../audit/evidence/bcf-structural-handoff-2026-07-17.json` | BCF T1 structural + dual consumers; CDE=NOT_VERIFIED |
| `../../audit/evidence/cde-import-proof/STATUS.json` | BCF T2 gate (must stay NOT_VERIFIED until real import) |
| `../../audit/evidence/samolet-sla-fixture-honesty-2026-07-17.json` | SLA schema 1.2.0, `claim_level=fixture_only` |
| `../../audit/evidence/customer-intake-gate.json` | All customer gates false until data arrives |
| `../../audit/reports/RED_TEAM_DELTA_2026_07_17.md` | Atomic post-remediation re-verification |

## Frozen / baseline (historical)

| File | Role |
|------|------|
| `pre-pilot-gates-evidence-2026-05-21.md` | Gates 1–4 |
| `pre-pilot-extraction-2026-05-21.json` | Extraction snapshot at tag era |
| `pre-pilot-runtime-baseline-2026-05-21.json` | Runtime APPROVED |
| `runtime-baseline-latest.json` | Rolling LOC/test/F1 snippet source |
| `benchmark-report-2026-05-20.md` | Historical benchmark (frozen line) |
| `benchmark-report-2026-05-21.md` | Rolling refresh |
| `pre-push-verification-2026-05-21.md` | Full verification lane |
| `public-surface-factcheck-2026-05-21.md` | Historical public-surface sweep (counts stale) |

## Samolet / pilot

| File | Role |
|------|------|
| `samolet-sla-pilot-moscow-2026-05-21.json` | **Superseded** fixture SLA 1.0 — cite July 17 honesty pack instead |
| `pre-pilot-bcf-handoff-2026-05-21.json` | Updated: structural_only; CDE NOT_VERIFIED |
| `samolet-typical-errors-mapping.json` | Catalog → rule_id coverage |
| `ablation-study-report.json` | A0–A3 |

## July 2026 tracks

| File | Role |
|------|------|
| `TRACK_A1_SECTION_PAIRING_2026_07_11.md` | PD↔RD canonical pairing |
| `TRACK_A2_NORM_PACKS_2026_07_11.md` | Norm packs CI/env |
| `TRACK_A3_INTAKE_PRECISION_2026_07_11.md` | Adjudication intake |
| `TRACK_A5_DEMO_PATH_2026_07_11.md` | Demo upload→analyze→BCF |
| `demo-path-pilot-moscow-2026-07-11.json` | A5 evidence (fixture loop) |
| `DRAWING_AI_WORLD_PRACTICE_2026_07.md` | OCR/CV claim boundary |

## Not in git

Customer packages, CDE screenshots — gitignored `docs/evidence/internal/` or outside repo. Tracked T2 gate: `audit/evidence/cde-import-proof/`. See [`../LOCAL_OPERATOR_ARTIFACTS.md`](../LOCAL_OPERATOR_ARTIFACTS.md).
