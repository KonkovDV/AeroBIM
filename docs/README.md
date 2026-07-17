---
title: "AeroBIM Documentation Map"
status: active
version: "0.7.0"
last_updated: "2026-07-17"
tags: [aerobim, documentation, navigation, reference]
---

# AeroBIM Documentation Map

## Purpose

Router for `AeroBIM/docs/`.

| Guide | Role |
|-------|------|
| [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md) | English vs Russian; no runglish |
| [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md) | Git vs local vs CI artifacts |
| [`evidence/README.md`](evidence/README.md) | Dated verification snapshots (+ July 17 honesty index) |
| [`archive/README.md`](archive/README.md) | Historical docs (`01`–`11`) |
| [`../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md) | **Claims wording SSOT** |
| [`../audit/reports/CRITICAL_BLOCKERS.md`](../audit/reports/CRITICAL_BLOCKERS.md) | Checkpoint **NO_GO** register (RT-001/002/003) |
| [`../audit/reports/RED_TEAM_DELTA_I0_I7_PASS3_2026_07_17.md`](../audit/reports/RED_TEAM_DELTA_I0_I7_PASS3_2026_07_17.md) | **Current** Red Team I0–I7 pass-3 |
| [`../audit/reports/RED_TEAM_TRACK_E_2026_07_17.md`](../audit/reports/RED_TEAM_TRACK_E_2026_07_17.md) | Track E residual honesty CLOSED |
| [`../audit/reports/AUDIT_I8C_TZ_V2_RESEARCH_2026_07_17.md`](../audit/reports/AUDIT_I8C_TZ_V2_RESEARCH_2026_07_17.md) | Audit I8c + TZ v2 + research re-verify |
| [`../audit/reports/AUDIT_IMPLEMENTATION_TZ_PORTS_I9_2026_07_17.md`](../audit/reports/AUDIT_IMPLEMENTATION_TZ_PORTS_I9_2026_07_17.md) | **I9 + TZ ports implementation audit** |
| [`../audit/reports/AUDIT_COMBAT_BACKENDS_I1_I9_2026_07_17.md`](../audit/reports/AUDIT_COMBAT_BACKENDS_I1_I9_2026_07_17.md) | Combat CAD/CV/I9/RT/MEP self-audit |
| [`../audit/reports/RED_TEAM_DELTA_2026_07_17.md`](../audit/reports/RED_TEAM_DELTA_2026_07_17.md) | Post-P0 delta (MEP DI cell superseded — see banner) |

## Tier 0 — SSOT (read first)

| File | Role |
|------|------|
| `REPRODUCIBILITY-2026.md` | FAIR/CODE, frozen tag, evidence manifest |
| `06-architecture-reference.md` | **SUPERSEDED** → use TARGET hybrid architecture |
| `architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md` | **Architecture SSOT** (ports, DeterminismGate, roadmap I0–I9) |
| `TIER0_INDEX.md` | **Tier-0 docs index** (live vs superseded) |
| `architecture/RESEARCH_ALIGNMENT_AEC_AI_2025_2026_07.md` | Literature 2025–2026 → AeroBIM (Blueprint, IfcLLM, ACC) |
| `architecture/EXECUTION_PLAN_I8_I9_2026_07.md` | **I8–I9** research-aligned advisory waves (**I9 = advisory scaffold**, not GraphRAG) |
| `architecture/EXECUTION_PLAN_NEXT_2026_07.md` | **Live** forward work plan — Track D/E/C/I + GO gate |
| `architecture/EXECUTION_PLAN_HYPERDEEP_2026_07.md` | Deep breakdown under NEXT |
| `archive/execution/EXECUTION_PLAN_I0_I2_2026_07.md` | **SUPERSEDED** I0–I5 wave log (stub in `architecture/`) |
| `archive/execution/EXECUTION_PLAN_I6_2026_07.md` | **SUPERSEDED** I6 wave log |
| `archive/execution/EXECUTION_PLAN_I7_2026_07.md` | **SUPERSEDED** I7 wave log |
| `../audit/reports/AUDIT_RED_TEAM_RT_A_H_2026_07_17.md` | RT-A…H remediations self-audit |
| `pilot-claim-boundary-2026.md` | Verified vs planned claims |
| `../audit/reports/CRITICAL_BLOCKERS.md` | Checkpoint NO_GO register |
| `samolet-techlab-alignment-2026.md` | Samolet R1–R15 traceability |
| `samolet-compliance-scorecard-2026.md` | Pilot closure sign-off |
| `PROJECT-AUDIT-2026-05-20.md` | Repository audit (May 2026) |
| `INDUSTRY_IMPROVEMENT_PLAN_2026_07.md` | **July 2026 industry-grade waves W0–W3** (soundness → openBIM → CDE) |
| `evidence/P1_ENGINEERING_DELIVERY_2026_07_10.md` | **P1 delivery** — norm packs, section pairing, precision harness |
| `evidence/TRACK_A1_SECTION_PAIRING_2026_07_11.md` | **Track A1** — canonical keys, multi-discipline PD↔RD |
| `evidence/TRACK_A2_NORM_PACKS_2026_07_11.md` | **Track A2** — norm packs CI schema + env/manifest |
| `evidence/TRACK_A3_INTAKE_PRECISION_2026_07_11.md` | **Track A3** — adjudication templates + intake runbook |
| `evidence/TRACK_A5_DEMO_PATH_2026_07_11.md` | **Track A5** — upload→analyze→BCF demo path on fixture |
| `partners/SAMOLET_TZ_REMAINING_TAILS_2026_07.md` | **Хвосты ТЗ Самолёта** — blockers vs engineering done |
| `partners/TECHLAB_TASK_07_READINESS_2026.md` | Task 07 readiness with fixture-only vocabulary |
| `evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md` | **OCR/CV/NLP posture** — July 2026 vs “AI reads like a human” |
| `tz/README.md` | **TZ Response Pack** — expert-assistant MVP |
| `tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md` | **ТЗ Задача 07 v2.0** (полный, Claims Lock) |
| `evidence/ACADEMIC_DEEP_AUDIT_2026_07_10.md` | Deep audit finding register (Jul 2026) |
| `evidence/FULL_AUDIT_FACTCHECK_2026_07_10.md` | Public-surface fact-check (Jul 2026) |

## Tier 1 — Active engineering (numbered)

| File | Role |
|------|------|
| `12-openrebar-provenance-decision-table.md` | OpenRebar severity policy |
| `13-academic-execution-plan-2026.md` | Standards roadmap A–C + status (see also July W0–W3 plan) |
| `14-enterprise-storage-foundation.md` | ObjectStore / Postgres foundation |
| `15-local-quality-gate.md` | CI-parity local commands (contributors) |

## Tier 1 — Pilot / Samolet / publication (2026)

| File | Purpose |
|---|---|
| `LOCAL_OPERATOR_ARTIFACTS.md` | Gitignored NDA/CDE paths |
| `partners/TECHLAB_SAMOLET_APPLICATION_2026.md` | TechLab application texts (task #07) |
| `partners/TECHLAB_TASK_07_READINESS_2026.md` | Official Task 07 mandate → AeroBIM readiness |
| `partners/SAMOLET_WHAT_WE_NEED_2026_07-ru.md` | **Что нужно от Самолёта** (kickoff handoff, RU) |
| `partners/SAMOLET_WHAT_WE_NEED_2026_07.md` | What Samolet must supply (EN SSOT) |
| `samolet-techlab-scorecard-2026.md` | Score ladder → 10 |
| `samolet-pilot-intake-checklist-2026.md` | Week 1 joint intake |
| `pilot-cde-handoff-2026.md` | CDE Scenario A/B |
| `samolet-kpi-adjudication-template-2026.md` | Wave 2 TP/FP log |
| `pilot-start-package-2026.md` | Kickoff (tag, gates, week 1) |
| `pilot-pre-pilot-gates-2026.md` | Technical gates before customer pilot |
| `pilot-kpi-protocol-2026.md` | KPI measurement protocol |
| `pilot-package-playbook-2026.md` | Moscow v1 input bundle |
| `pilot-deployment-2026.md` | VM/Docker deployment |
| `pilot-execution-runbook-2026.md` | 8–12 week rhythm |
| `pilot-weekly-log-2026.md` | Weekly KPI / TP-FP template |
| `pilot-frozen-tag-protocol-2026.md` | Reproducible pilot tags |
| `pilot-case-study-report-2026.md` | Case study KPI template (EN) |
| `pilot-case-study-report-ru.md` | Interview questions (RU) |
| `post-pilot-fork-2026.md` | Enterprise vs research branch |
| `post-pilot-go-no-go-memo-2026.md` | Branch A/B/C decision |
| `academic-pilot-evidence-2026.md` | Pilot evidence dossier |
| `academic-publication-evidence-2026.md` | Publication bundle |
| `annotation-protocol-2026.md` | RU/EN extraction annotation + IAA rules |
| `tz/TZ_COMPLIANCE_MATRIX_2026.md` | TZ ↔ AeroBIM compliance matrix |
| `tz/TZ_ARCHITECTURE_REQUIREMENTS_2026.md` | TZ architecture TBD fill |
| `tz/TZ_BUILD_AND_QUALITY_2026.md` | TZ build/quality TBD fill |
| `tz/TZ_SOLUTION_IMAGE_AND_PRESENTATION_2026.md` | Demo script + slide outline |
| `tz/TZ_ACCOMPANYING_DOCS_2026.md` | Accompanying docs checklist |
| `benchmark-report-template.md` | Supplementary report skeleton |
| `manuscript-draft-2026.md` | Paper draft outline |
| `contributor-git-2026.md` / `contributor-git-ru.md` | Single-author commits |
| `github-readiness-audit-2026-05-20.md` | Pre-push fact-check |
| `optional-adapters-smoke-2026.md` | clash / docling smoke |

## Tier 2 — Archive

Moved to [`archive/`](archive/): `01`–`05`, `07`–`11` (MicroPhoenix extraction, rebaseline, April fact-check, RU academic audit). Stub files at old paths redirect here.

**Superseded by:** Tier 0 + [`PROJECT-AUDIT-2026-05-20.md`](PROJECT-AUDIT-2026-05-20.md) for current audit state.

## Recommended reading order (new contributors)

1. [`06-architecture-reference.md`](06-architecture-reference.md)
2. [`15-local-quality-gate.md`](15-local-quality-gate.md)
3. [`REPRODUCIBILITY-2026.md`](REPRODUCIBILITY-2026.md)
4. [`pilot-claim-boundary-2026.md`](pilot-claim-boundary-2026.md)
5. [`tz/README.md`](tz/README.md) (if preparing the expert-assistant TZ)
6. [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) (if working on Samolet pilot)

## Rules for future docs

- Update the authority source before mirrors or summaries.
- New historical material goes under `archive/`; do not grow the docs root with superseded plans.
- One language per file — see [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md).
- No speculative runtime claims without repo proof or authoritative external evidence.

## Drawing AI posture

July 2026: [evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
