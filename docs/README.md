---
title: "AeroBIM Documentation Map"
status: active
version: "0.5.0"
last_updated: "2026-05-21"
tags: [aerobim, documentation, navigation, reference]
---

# AeroBIM Documentation Map

## Purpose

Router for `AeroBIM/docs/`.

| Guide | Role |
|-------|------|
| [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md) | English vs Russian; no runglish |
| [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md) | Git vs local vs CI artifacts |
| [`evidence/README.md`](evidence/README.md) | Dated verification snapshots |
| [`archive/README.md`](archive/README.md) | Historical docs (`01`–`11`) |

## Tier 0 — SSOT (read first)

| File | Role |
|------|------|
| `REPRODUCIBILITY-2026.md` | FAIR/CODE, frozen tag, evidence manifest |
| `06-architecture-reference.md` | Technical architecture |
| `pilot-claim-boundary-2026.md` | Verified vs planned claims |
| `samolet-techlab-alignment-2026.md` | Samolet R1–R15 traceability |
| `samolet-compliance-scorecard-2026.md` | Pilot closure sign-off |
| `PROJECT-AUDIT-2026-05-20.md` | Repository audit (May 2026) |

## Tier 1 — Active engineering (numbered)

| File | Role |
|------|------|
| `12-openrebar-provenance-decision-table.md` | OpenRebar severity policy |
| `13-academic-execution-plan-2026.md` | Standards roadmap A–C + status |
| `14-enterprise-storage-foundation.md` | ObjectStore / Postgres foundation |
| `15-local-quality-gate.md` | CI-parity local commands (contributors) |

## Tier 1 — Pilot / Samolet / publication (2026)

| File | Purpose |
|---|---|
| `LOCAL_OPERATOR_ARTIFACTS.md` | Gitignored NDA/CDE paths |
| `partners/TECHLAB_SAMOLET_APPLICATION_2026.md` | TechLab application texts |
| `samolet-techlab-scorecard-2026.md` | Score ladder 7.6 → 10 |
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
| `annotation-protocol-2026.md` | RU extraction annotation rules |
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
5. [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md) (if working on Samolet pilot)

## Rules for future docs

- Update the authority source before mirrors or summaries.
- New historical material goes under `archive/`; do not grow the docs root with superseded plans.
- One language per file — see [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md).
- No speculative runtime claims without repo proof or authoritative external evidence.
