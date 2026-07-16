---
title: "TechLab Samolet Task 07 Readiness 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-17"
tags: [aerobim, techlab, samolet, task-07, readiness]
---

# Task 07 readiness — automated verification of PD/RD

**Official task:** Система автоматизированной верификации проектной и рабочей документации — **Задача 07**  
**Sponsor quote (Artsrun Gevorkyan):** automatic checking is not about replacing the engineer — it is about ensuring no obvious error reaches the construction site.  
**Prize:** paid pilot testing fund **2 000 000 ₽**  
**Task page:** https://i.moscow/techlab/samolet  
**Checkpoint:** **`NO_GO`** until RT-001/002/003 ([`../../audit/reports/CRITICAL_BLOCKERS.md`](../../audit/reports/CRITICAL_BLOCKERS.md)).  
**Traceability:** [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) · [`../tz/README.md`](../tz/README.md) · [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md) · [`../../audit/reports/CLAIMS_LOCK_2026_07_17.md`](../../audit/reports/CLAIMS_LOCK_2026_07_17.md)

Status vocabulary: `VERIFIED_FIXTURE_ONLY` | `PARTIAL` | `FOUNDATION` | `BLOCKED_BY_CUSTOMER_DATA` | `MISSING` | `NOT_VERIFIED`.

## 1. Official mandate → AeroBIM

| Task 07 requirement | AeroBIM today | Status |
|---------------------|---------------|--------|
| Work with **2D drawings** | Structured annotations + PDF/OCR baseline + 2D overlay | PARTIAL (CV deferred; OCR optional-extra) |
| Work with **BIM models** | IFC + IDS + schema pre-gate + optional clash | VERIFIED_FIXTURE_ONLY |
| Work with **TZ + calculations** | Narrative/structured extract + cross-doc + OpenRebar **сверка** | PARTIAL (correctness NOT_IMPLEMENTED) |
| Compare docs vs calcs / TZ / sections / norms | Cross-doc + IDS + JSON norm packs + PD↔RD pairing | PARTIAL (customer pack TBD) |
| Detect clashes | IfcClash + `SPATIAL-*`; `require_clash` fail-closed | PARTIAL (generic; MEP NOT_VERIFIED) |
| Calc / dimension / area errors | Quantity algebra + cross-doc | VERIFIED_FIXTURE_ONLY (bounded) |
| Logic gaps / missing elements | IDS `exists` + property checks | VERIFIED_FIXTURE_ONLY |
| Highlight problem zones | `problem_zone` + drawing overlay | VERIFIED_FIXTURE_ONLY |
| Prioritize remarks | `compute_issue_priority` + Samolet profile | VERIFIED_FIXTURE_ONLY |
| Generate designer comments | RU/EN templates + HITL edit | VERIFIED_FIXTURE_ONLY |
| Speed up review | SLA rail ≤30 min on agreed pack | FIXTURE_ONLY measured; customer pack BLOCKED |
| Expert remains in the loop | Claim boundary + review-events / adjudication | VERIFIED_FIXTURE_ONLY |
| MVP with visualization + reports | Browser shell + JSON/HTML/BCF **export** | VERIFIED_FIXTURE_ONLY (CDE import NOT_VERIFIED) |
| Resources: PD/RD, BIM, TZ/standards, typical errors | Appendix + catalog + mapping tool | PARTIAL → customer intake |
| Competencies BIM/CAD, CV/OCR, AI/ML | BIM/OCR when extras present; CV/LLM advisory only | honest split |
| Stack at team discretion | Python FastAPI + React + openBIM | VERIFIED_FIXTURE_ONLY |

## 2. Product stance (matches sponsor quote)

> Automation reduces the volume of manual checking; **expert validation of results remains**.

AeroBIM is **decision-support**, not a licensed-engineer replacement. Sign-off path is **deterministic** (IFC/IDS/cross-doc/clash/OCR+regex). Computer Vision / LLM are **advisory** and do not set `summary.passed` without HITL.

## 3. MVP delivered vs pilot ask (2M ₽)

### Already in repo (demo-ready)

- Multimodal analyze API + capabilities honesty  
- Browser review: 3D IFC + 2D overlay + severity filter + remark edit  
- Multipart upload (`POST /v1/uploads`)  
- BCF 2.1/3.0 export + OpenCDE push foundation  
- **Track A5 demo path** — `aerobim-run-demo-path` (upload→analyze→HTML/BCF on fixture)  
- Extraction F1 gate, ablation A0–A3, SLA measurement tool  
- Backend pytest suite (see latest local run; optional extras may skip)

### Needs Samolet pilot corpus (cannot fake in git)

Detailed ask (world + RU practice, July 2026):  
[`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](SAMOLET_WHAT_WE_NEED_2026_07-ru.md) (send to Samolet) · [`SAMOLET_WHAT_WE_NEED_2026_07.md`](SAMOLET_WHAT_WE_NEED_2026_07.md)

1. Customer PD/RD/BIM pack (week-1 intake)  
2. Customer-approved residential norms / IDS pack (synthetic AR template is not sign-off)  
3. Customer confirmation of typical-errors catalog (≥20 engineering patterns already scaffolded)  
4. CDE BCF roundtrip evidence  
5. Engineer TP/FP adjudication on customer corpus via precision harness (TZ «>90%» only after this)  
6. Signed scope memo + ≥2 adjudicators + manual baseline hours  

### Pilot success criteria (contract)

| Criterion | Target |
|-----------|--------|
| Package SLA | ≤ **30 min** on **agreed** corpus |
| Confirmed findings | TP/(TP+FP) ≥ **60%** interim |
| Review time saved | ≥ **20%** vs manual baseline |
| CDE handoff | BCF 2.1 visible in customer tool |
| Expert accountability | Adjudication log signed |

## 4. Pitch (one paragraph, RU)

AeroBIM — открытый мультимодальный ассистент проверки ПД/РД: IFC, IDS, ТЗ, расчёты и 2D-доказательства в одном детерминированном контуре. Подсветка проблемных зон, приоритизация и генерация замечаний (RU/EN), выгрузка BCF. Система ускоряет эксперта и не заменяет его. Для пилота TechLab: адаптация под типы документов Самолёта, каталог типовых ошибок, SLA ≤30 мин на согласованном комплекте, импорт BCF в CDE.

## 5. Ask

Primary handoff document: [`SAMOLET_WHAT_WE_NEED_2026_07-ru.md`](SAMOLET_WHAT_WE_NEED_2026_07-ru.md).

1. TechLab pilot budget (**2 000 000 ₽**) + named Samolet owner  
2. One residential (or agreed) document package + IDS/rule pack + typical-error list (≥20)  
3. Week-1 CDE import path + **two** adjudicating engineers + manual baseline hours  
4. Written scope memo: norms = **agreed rule sets**; IDS ≠ geometry; CV not MVP sign-off  
5. NDA / secure transfer channel (no public git) 

## 6. Experts (task page)

| Name | Role |
|------|------|
| Artsrun Gevorkyan | Head of Moscow-region development block (sponsor quote) |
| Alexander Gorelik | Director, technological customer directorate |
| Artur Khasanov | Head of project office |

## 7. Do not claim on application form

- Production rollout at Samolet  
- Full SP/GOST automation  
- Autonomous sign-off  
- Clash/inconsistency accuracy **>90%** without labeled adjudication  
- “True CV” as the pilot sign-off path (OCR baseline only)

## Drawing AI posture (retained local SSOT)

July 2026: [../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md](../evidence/DRAWING_AI_WORLD_PRACTICE_2026_07.md).
