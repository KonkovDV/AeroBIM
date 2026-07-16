---
title: "TechLab Samolet Application 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-10"
tags: [aerobim, techlab, samolet, application]
---

# AeroBIM — TechLab Moscow (Samolet task #07)

**Partner:** Samolet (Московский инновационный кластер / TechLab)  
**Task:** Система автоматизированной верификации проектной и рабочей документации — **Задача 07**  
**Task page:** https://i.moscow/techlab/samolet  
**Prize:** платное пилотное тестирование **2 000 000 ₽**  
**Scorecard:** [`../samolet-techlab-scorecard-2026.md`](../samolet-techlab-scorecard-2026.md)  
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

**Required competencies covered:** BIM/CAD (IFC/IDS) ✅ · OCR baseline ✅ · CV/AI-ML as advisory roadmap (not sign-off) — stated honestly.

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

| Name | Role |
|------|------|
| Artsrun Gevorkyan | Head of Moscow-region development block |
| Alexander Gorelik | Director, technological customer directorate |
| Artur Khasanov | Head of project office |
