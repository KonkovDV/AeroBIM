---
title: "Samolet TechLab Scorecard 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-10"
tags: [aerobim, samolet, techlab, scorecard]
---

# Scorecard: AeroBIM vs Samolet TechLab (task #07)

**Task:** Система автоматизированной верификации ПД/РД — Задача 07  
**Task page:** [i.moscow/techlab/samolet](https://i.moscow/techlab/samolet)  
**Prize:** 2 000 000 ₽ paid pilot  
**Traceability SSOT:** [`samolet-techlab-alignment-2026.md`](samolet-techlab-alignment-2026.md)  
**Readiness:** [`partners/TECHLAB_TASK_07_READINESS_2026.md`](partners/TECHLAB_TASK_07_READINESS_2026.md)  
**Closure target (10/10):** [`samolet-compliance-scorecard-2026.md`](samolet-compliance-scorecard-2026.md)

## Headline scores

| Audience | Score today | Score after pilot |
|----------|-------------|-------------------|
| TechLab jury (architecture fit) | **8,2–8,5** | **9,5+** |
| Samolet technical pilot | **7,5–8,0** | **10,0** (agreed scope) |
| Combined (honest) | **8,0** | **10,0** |

## R1–R15 ladder (today → target)

| ID | Requirement | Today | Target | Wave |
|----|-------------|------:|-------:|------|
| R1 | 2D drawings | 7,5 | 9,5 | 1–2 |
| R2 | BIM models | 9,5 | 10 | 0 |
| R3 | TZ + calculations | 8,5 | 9,5 | 1 |
| R4 | Norms / rules | 6,5 | 9 | 1 |
| R5 | Collisions | 7,5 | 9,5 | 1 |
| R6 | Areas / dimensions | 8,5 | 9,5 | 2 |
| R7 | Logic / missing | 8,5 | 9,5 | 1 |
| R8 | Problem zones | 8,5 | 9,5 | 1 |
| R9 | Prioritization | 8,5 | 10 | 0 |
| R10 | Designer comments | 8,5 | 9,5 | 0 (P0 done) |
| R11 | Faster review | 6,5 | 10 | 2 |
| R12 | Expert in loop | 10 | 10 | 0 |
| R13 | MVP + reports | 9,5 | 10 | 0 (upload + UI) |
| R14 | Typical errors | 4,5 | 10 | 1–2 |
| R15 | SLA ≤ 30 min | 7,5 | 10 | 2 |

## Pitch outline (6 slides)

1. **Pain** — late design errors cost rework (Gevorkyan quote from task page).
2. **Solution** — deterministic multimodal QA: IFC + IDS + TZ + calc + 2D → BCF.
3. **Evidence** — 328 tests, F1 ≥ 0,70 gate, SLA rail, ablation A0–A3, TZ response pack.
4. **Product stance** — assistive automation (expert in the loop); deterministic sign-off; CV/LLM advisory only.
5. **Pilot** — one corpus, one CDE path, KPI memo (60% TP, 20% time, 30 min SLA).
6. **Ask** — TechLab pilot budget 2M ₽ + Samolet corpus + week-1 CDE import.

## Program scope (3.5 months)

| Month | Deliverable |
|-------|-------------|
| 1 | Intake, CDE scenario A, norm pack, typical-errors catalog filled |
| 2 | Noise tuning, TP/FP ≥ 55%, SLA on customer pack v1 |
| 3 | KPI sign-off, case study N=1, demo-day package |

## Claims for application form

**Short (≤500 chars):**  
AeroBIM — open multimodal BIM validation: IFC, IDS 1.0, specifications, calculations, and 2D evidence in one deterministic pipeline. Decision-support for reviewers (not replacement). BCF 2.1 export, browser review, reproducible metrics (F1 ≥ 0.70). TechLab scope: adapt to Samolet document types, typical-error catalog, ≤30 min SLA on agreed package, CDE handoff.

**Do not claim:** production rollout at Samolet, full SP/GOST automation, autonomous sign-off, >90% accuracy without adjudication.

## Links

- Application packet: [`partners/TECHLAB_SAMOLET_APPLICATION_2026.md`](partners/TECHLAB_SAMOLET_APPLICATION_2026.md)
- Task 07 readiness: [`partners/TECHLAB_TASK_07_READINESS_2026.md`](partners/TECHLAB_TASK_07_READINESS_2026.md)
- Intake checklist: [`samolet-pilot-intake-checklist-2026.md`](samolet-pilot-intake-checklist-2026.md)
- CDE handoff: [`pilot-cde-handoff-2026.md`](pilot-cde-handoff-2026.md)
