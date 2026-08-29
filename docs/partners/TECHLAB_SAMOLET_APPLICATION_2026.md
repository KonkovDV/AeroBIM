<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "TechLab Samolet Application 2026"
status: active
version: "1.1.3"
last_updated: "2026-08-29"
tags: [aerobim, techlab, samolet, application]
---

# AeroBIM — TechLab Moscow (Samolet Samolet PD/RD verification task)

**Partner:** Samolet (Московский инновационный кластер / TechLab)  
**Task:** Система автоматизированной верификации проектной и рабочей документации — **задаче Самолёта по верификации ПД/РД**  
**Task page:** https://i.moscow/techlab/samolet  
**Prize:** платное пилотное тестирование **2 000 000 ₽** (условия — соглашение Партнёра и Фонда)  
**Eligibility:** FAQ i.moscow/techlab — физлица или команда 1–10; **ИП не требуется для участия**.  
**Readiness / claims:** [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md) · [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)  
**Readiness memo:** [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md)  
**Alignment:** [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md)  
**TZ pack:** [`../tz/README.md`](../tz/README.md)

## Sponsor framing (use in pitch)

> Одна пропущенная ошибка на этапе проектирования может погубить значительную часть проекта. Автоматическая проверка — это не про замену инженера, это про то, чтобы ни одна очевидная ошибка не доходила до стройплощадки.  
> — Арцрун Геворкян, глава девелоперского блока Московского региона

AeroBIM product stance matches this quote: **assistive automation**, expert remains accountable.

## Application texts

**Project name:** AeroBIM

**Short description (EN, ≤500 chars):**  
AeroBIM is an open multimodal assistant for PD/RD verification: IFC, IDS, design briefs, calculations, and 2D evidence in one deterministic pipeline. Highlights problem zones, prioritizes remarks (RU/EN), exports BCF. Decision-support for reviewers — not a replacement. Target: ≤30 min on an agreed package; pilot adapts to Samolet document types and typical-error catalog.

**Short description (RU):**  
AeroBIM — открытый мультимодальный ассистент проверки ПД/РД: IFC, IDS, ТЗ, расчёты и 2D-доказательства в одном детерминированном контуре. Подсветка зон, приоритизация и генерация замечаний (RU/EN), BCF. Ускоряет эксперта, не заменяет его. Цель: ≤30 мин на согласованном комплекте; пилот — типы документов Самолёта и каталог типовых ошибок.

**Full description:** README + [`../samolet-techlab-alignment-2026.md`](../samolet-techlab-alignment-2026.md) (R1–R15) + [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md).

**Novelty:** openBIM contracts (IFC/IDS/BCF) + cross-document checks + ε-tolerance algebra; ablation A0–A3; reproducibility per [`../REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md); honest CV/LLM boundary (advisory only).

**Required competencies covered:** BIM/CAD (IFC/IDS) ✅ · OCR baseline ✅ · CV/AI-ML as advisory roadmap (not sign-off) — stated honestly. Public LETI text (30.04.2026) asks for **both** scientific and engineering (IT/ML/data) competencies; empty role matrix: [`K1_ROLE_MATRIX_TEMPLATE_2026_08.md`](K1_ROLE_MATRIX_TEMPLATE_2026_08.md). Person cells stay empty in git.

**Appendix 4 public table (LETI, 30.04.2026):** row **6** is this Partner task (paid pilot 2M ₽). Neighbouring row 7 is a different partner. Historical filename «07» is not that number. Map: [`../quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md`](../quality/MIK_CRITERION_EVIDENCE_MAP_2026_08.md).

**Stack (team choice):** Python 3.12 + FastAPI + React review shell + IfcOpenShell / IfcTester / optional IfcClash.

## Pilot success criteria

1. BCF 2.1 visible in customer CDE  
2. TP/(TP+FP) ≥ 60% on agreed scope  
3. Review time ≥ 20% savings vs baseline  
4. SLA ≤ 30 min on agreed package  
5. Typical-errors catalog ≥ 20 patterns mapped to rules  

## Attachments for submission

1. GitHub README + browser review screenshot (2D overlay + remark panel)  
2. [`TECHLAB_TASK_07_READINESS_2026.md`](TECHLAB_TASK_07_READINESS_2026.md)  
3. [`../REPRODUCIBILITY-2026.md`](../REPRODUCIBILITY-2026.md)  
4. [`../pilot-claim-boundary-2026.md`](../pilot-claim-boundary-2026.md)  
5. Evidence: extraction F1 / SLA fixture / ablation table under `docs/evidence/`

## Experts (task page)

The public task page is **not** the signed commission roster. A 29.08 owner
briefing of Fund order П-01-ОД-52-1/26 adds a Partner information-modelling
seat the catalog still omits. Prepare to the signed order. The sponsor quote
below is **not** attested as commission chair.

| Name | Role |
|------|------|
| Artsrun Gevorkyan | Head of Moscow-region development block (sponsor quote) |
| Alexander Gorelik | Director, technological customer directorate |
| Artur Khasanov | Head of project office |
