<!-- claims-lint: allow-file reason="Claims-boundary doc citing forbidden phrases as non-claims per pilot-claim-boundary / Claims Lock (WP-A5)" -->
---
title: "Samolet Pilot Protocol 2026"
status: active
version: "1.1.0"
last_updated: "2026-07-24"
claim_boundary: "Protocol only. Thresholds are parameters for customer agreement. Checkpoint GO; customer_go false until RT-001/002/003."
---

# Pilot Protocol — ГК «Самолёт» × AeroBIM TechLab Task 07

Параллельный план Checkpoint #2: `pilot/PARALLEL_WORKPLAN_CHECKPOINT2_2026_08.md`.  
Инструкция разметчиков: [`pilot/EXPERT_LABELING_INSTRUCTION_2026.md`](pilot/EXPERT_LABELING_INSTRUCTION_2026.md).

## Goal

Evidence-driven bounded pilot: measure whether AeroBIM reduces expert verification effort on an agreed package **without false-green Shared-gate** and with full finding provenance.

## Non-goals

- Replace licensed engineer.
- Claim >90% / customer SLA / MEP delivered / native DWG / calc solver / CDE-ready BCF without artifacts.

## Pilot package composition (состав комплекта)

| Компонент | Обязательность | Форматы (допустимые) |
|-----------|----------------|----------------------|
| ПД | По scope memo | PDF (+ IFC если в обмене) |
| РД | Рекомендуется пара ПД↔РД | PDF / IFC |
| IFC | Обязателен для BIM-проверок | IFC2X3 / IFC4 (см. compatibility matrix) |
| ТЗ / EIR-фрагмент | Обязателен для TZ/IDS | PDF / DOCX / structured JSON |
| Расчётные материалы | Если сверка в scope | PDF / таблица + provenance |
| Нормативные документы / pack | RT-002 | Machine-readable norm pack + ссылки на СП |

**Границы пилота** фиксируются в scope memo: разделы, стадии (П/Р), типы проверок, версии IFC, что *не* проверяем (DWG native, calc solver, полный MEP и т.д.).

## Сценарий end-to-end

```text
загрузка → проверка (AeroBIM) → экспертная валидация (dual-blind)
  → исправление (проектная команда) → повторная проверка → BCF handoff (если в scope)
```

## Классы ошибок и уровни

| Класс | Critical / Warning / Info |
|-------|---------------------------|
| clash | Critical при обязательном clearance; иначе Warning/Info |
| attribute | Critical если IDS/обязательный критерий; иначе Warning |
| dimension / area | По согласованной допусковой политике |
| cross_document | Critical при противоречии ПД↔РД в scope |
| missing_element | Critical если `exists` в утверждённом pack |

Детали разметки TP/FP/FN и κ: инструкция экспертов.

## Agreed inputs (Phase 0 — blocking)

| Input | Owner | Notes |
|---|---|---|
| NDA + scope memo | Samolet + AeroBIM | Disciplines, stage П/Р, in/out of auto-check |
| Customer package (IFC/PDF/ТЗ/calc) | Samolet | `samples/customer/` local only — never git |
| Approved norm/IDS pack + approval object | Samolet | RT-002 |
| Federated MEP pack + clearance rules (if MEP in scope) | Samolet | RT-003 |
| ≥2 named adjudicators | Samolet | Dual-independent |
| Manual baseline hours | Samolet | Same package |

Intake gate: `aerobim-validate-customer-intake-gate` · [`../audit/evidence/customer-intake-gate.json`](../audit/evidence/customer-intake-gate.json).

## Threshold parameters (agree in writing — do not invent GO)

| Parameter | Suggested starting point | Binding? |
|---|---|---|
| Interim precision TP/(TP+FP) | ≥ 0.60 | Agree with Samolet |
| Critical-error recall | Agree per class | Agree |
| Cohen’s κ / Krippendorff’s α | ≥ 0.60 suggested | Agree |
| Package wall-clock | ≤ 30 min on **agreed** pack | Measure, then claim |
| Review-time reduction | ≥ 20% vs baseline | Measure |
| Max false-positive burden | Agree | Agree |

## Phases

```text
Phase 0  Agree corpus + rules + thresholds + frozen split
Phase 1  Manual baseline (hours, findings, cycles)
Phase 2  AeroBIM run offline (no production workflow influence)
Phase 3  Dual adjudication TP/FP/FN + κ/α
Phase 4  Controlled BCF handoff + import evidence (if in scope)
Phase 5  Expand / narrow / stop decision
```

### Phase 2 runtime

```bash
cd backend
python -m aerobim.tools.export_evidence_bundle \
  --pack ../samples/customer/<agreed-pack>.json \
  --output ../artifacts/pilot-evidence/<run-id>
```

Bundle must include: file hashes, report JSON/HTML, findings, capability coverage, timings, code version, reproduction README.

### Stop / narrow rules

Stop or narrow if: expert distrust; critical misses above threshold; unstable mandatory checks; missing provenance; time not scaling; no effect vs baseline; customer cannot supply corpus/rules.

## Roles

| Role | Responsibility |
|---|---|
| Tech lead | Runtime, evidence bundle, fail-closed profile |
| openBIM lead | IFC/IDS/clash/BCF |
| Adjudicators (≥2) | TP/FP labels; no LLM-as-adjudicator |
| Samolet sponsor | Scope memo; CDE import proof owner |
| Security | Closed-contour review before production data |

## Success / expansion

Expand only if: mandatory checks stable; findings have source+evidence; quality measured on frozen set; critical classes meet agreed recall; time measured on real pack; effect vs baseline documented.

Product checkpoint remains **NO_GO** until RT-001/002/003 close with evidence — engineering remediations do not flip checkpoint.
