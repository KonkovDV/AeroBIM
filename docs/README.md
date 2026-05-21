---
title: "AeroBIM Documentation Map"
status: active
version: "0.4.0"
last_updated: "2026-05-21"
tags: [aerobim, documentation, navigation, reference]
---

# AeroBIM Documentation Map

## Purpose

Router for `AeroBIM/docs/`. **Language policy:** [`LANGUAGE-POLICY-2026.md`](LANGUAGE-POLICY-2026.md). **What belongs in git vs local-only:** [`REPOSITORY-HYGIENE-2026.md`](REPOSITORY-HYGIENE-2026.md). **Evidence index:** [`evidence/README.md`](evidence/README.md).

## Tier 0 — SSOT (read first)

| File | Role |
|------|------|
| `LANGUAGE-POLICY-2026.md` | English vs Russian docs; no runglish |
| `REPOSITORY-HYGIENE-2026.md` | Public vs gitignored vs CI artifacts |
| `REPRODUCIBILITY-2026.md` | FAIR/CODE, frozen tag, evidence manifest |
| `06-architecture-reference.md` | Technical architecture |
| `pilot-claim-boundary-2026.md` | Verified vs planned claims |
| `samolet-techlab-alignment-2026.md` | Samolet R1–R15 traceability |
| `samolet-compliance-scorecard-2026.md` | Pilot closure sign-off |

## Tier 1 — Active pilot / Samolet (2026)

See table **Pilot and Publication** below.

## Tier 2 — Archive / reference (numbered docs)

Historical MicroPhoenix extraction and rebaseline plans (`01`–`15`). Still accurate as reference; superseded for day-to-day pilot work by Tier 0 + Samolet docs. Prefer `PROJECT-AUDIT-2026-05-20.md` over `10-academic-audit` for current audit state.

## Recommended Reading Order

1. `06-architecture-reference.md` — canonical architecture reference.
2. `05-fact-check-audit.md` — verified standards and repository-state evidence.
3. `10-academic-audit-and-recommendations-ru.md` — current academic-level assessment and recommendations.
4. `11-rebaseline-execution-plan.md` — phased work plan and delivery status.
5. `12-openrebar-provenance-decision-table.md` — advisory vs enforced escalation table for reinforcement provenance findings.
6. `14-enterprise-storage-foundation.md` — current B.1 storage foundation, env knobs, and rollout boundary.
7. `08-microphoenix-adoption-matrix.md` — exact keep/adapt/defer/reject decisions.
8. `09-implementation-and-verification-rails.md` — how work should be delivered and verified.
9. `04-atomic-backlog.md` — execution-ready backlog.
10. `03-openbim-landscape.md` — standards, tooling, and competitor frame.
11. `07-project-skeleton.md` — current filesystem skeleton and active vs placeholder surfaces.
12. `15-local-quality-gate.md` — CI-parity local formatting/lint/type/test commands.
13. `01-strategy-and-plan.md` — product thesis and phased plan.

## Pilot and Publication (2026)

| File | Purpose |
|---|---|
| `LOCAL_OPERATOR_ARTIFACTS.md` | Gitignored NDA/CDE paths (operator only) |
| `partners/TECHLAB_SAMOLET_APPLICATION_2026.md` | TechLab application texts (in-repo) |
| `REPRODUCIBILITY-2026.md` | FAIR/CODE reproducibility SSOT, frozen tag, evidence manifest |
| `samolet-techlab-alignment-2026.md` | Samolet TechLab requirements traceability + May 2026 openBIM anchors |
| `samolet-techlab-scorecard-2026.md` | Score ladder 7.6 → 10 for jury / pilot |
| `samolet-compliance-scorecard-2026.md` | Closure SSOT (R1–R15 sign-off) |
| `samolet-pilot-intake-checklist-2026.md` | Week 1 joint intake |
| `pilot-cde-handoff-2026.md` | CDE Scenario A/B |
| `samolet-kpi-adjudication-template-2026.md` | Wave 2 TP/FP log |
| `pilot-start-package-2026.md` | Kickoff one-pager (tag, gates, week 1 actions) |
| `pilot-claim-boundary-2026.md` | Verified vs planned claims for pilot communications |
| `pilot-package-playbook-2026.md` | Moscow v1 input bundle and BCF checklist |
| `pilot-pre-pilot-gates-2026.md` | Technical gates before customer pilot |
| `pilot-kpi-protocol-2026.md` | KPI measurement protocol |
| `pilot-deployment-2026.md` | Standalone VM/Docker deployment |
| `pilot-case-study-report-2026.md` | Section 5 case study KPI template |
| `post-pilot-fork-2026.md` | Enterprise vs research branch after pilot |
| `academic-pilot-evidence-2026.md` | Pilot-phase evidence dossier |
| `academic-publication-evidence-2026.md` | Publication bundle commands and artifacts |
| `annotation-protocol-2026.md` | RU extraction benchmark annotation rules |
| `benchmark-report-template.md` | ITcon-style supplementary report skeleton |
| `manuscript-draft-2026.md` | Paper draft outline (method + case study) |
| `CITATION.bib` | BibTeX entries for reuse |
| `contributor-git-2026.md` | Single-author commits; no co-author trailers |
| `PROJECT-AUDIT-2026-05-20.md` | Deep audit, fact-check, hygiene findings |
| `github-readiness-audit-2026-05-20.md` | Pre-push fact-check and evidence table |
| `pilot-execution-runbook-2026.md` | 8–12 week pilot weekly rhythm |
| `pilot-weekly-log-2026.md` | Weekly KPI / TP-FP log template |
| `pilot-frozen-tag-protocol-2026.md` | Reproducible pilot release tags |
| `post-pilot-go-no-go-memo-2026.md` | Branch A/B/C decision template |
| `optional-adapters-smoke-2026.md` | clash / docling extra verification |

## Document Modes

| File | Dominant mode | Purpose |
|---|---|---|
| `01-strategy-and-plan.md` | explanation | product thesis, phases, success criteria |
| `02-microphoenix-extraction.md` | explanation | extraction logic and architectural translation |
| `03-openbim-landscape.md` | reference + explanation | external standards, tools, and market frame |
| `04-atomic-backlog.md` | reference | executable task inventory |
| `05-fact-check-audit.md` | evidence | verified claims and corrected findings |
| `06-architecture-reference.md` | reference | canonical technical architecture |
| `07-project-skeleton.md` | reference | directory structure and placeholder policy |
| `08-microphoenix-adoption-matrix.md` | reference | exact extraction decisions from MicroPhoenix |
| `09-implementation-and-verification-rails.md` | how-to | operational build and verification discipline |
| `10-academic-audit-and-recommendations-ru.md` | explanation + evidence | current academic audit and prioritised recommendations |
| `11-rebaseline-execution-plan.md` | how-to | current phased execution plan and wave tracking |
| `12-openrebar-provenance-decision-table.md` | reference + how-to | enforced/advisory provenance severity policy for OpenRebar integration |
| `13-academic-execution-plan-2026.md` | how-to + roadmap | standards-aligned execution plan with iteration status |
| `14-enterprise-storage-foundation.md` | reference + how-to | B.1 storage foundation, env controls, rollout boundary |
| `15-local-quality-gate.md` | how-to | CI-parity local quality commands and formatter recovery flow |

## Rules For Future Docs Work

- update the authority source before mirrors or summaries;
- preserve fact-check evidence separately from the active architectural reference;
- do not add speculative runtime claims without either repo proof or authoritative external evidence;
- keep frontend claims aligned with the active review shell and keep the Revit-plugin explicitly boundary-first until that runtime exists.