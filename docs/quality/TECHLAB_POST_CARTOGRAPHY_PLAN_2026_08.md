<!-- claims-lint: allow-file reason="Post-cartography execution plan; TZ 90%/SLA/MEP/RT CLOSED blocked; Checkpoint NO_GO" -->
---
title: "Post-cartography execution plan — seven TechLab tasks"
date: "2026-08-27"
last_updated: "2026-08-27"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_level: coverage_map_only
detected_count: 0
claim_boundary: >
  Execution plan after a local NDA coverage map. Not TP/FP. Not product
  accuracy. Not customer SLA. Not MEP delivered. Checkpoint NO_GO.
  Meets/Does-not are forbidden as customer verdicts until dual raters + κ.
---

# План после карты семи задач

**Вопрос.** Что делать дальше, когда семь сравнений «ТЗ для Техлаб» уже разложены по ячейкам, а критерий каждой — Uncertain.

**Не склеивать четыре бумаги:** публичный бриф ТЗ v1 (6 стр.); ТЗ v2 (ТР-1…62, capability движка); семь задач сравнения (intra-project); проектное ТЗ объекта (проза II/C0, ТЭП, K0 — не IDS).

Карта ячеек: [`TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md`](TECHLAB_SEVEN_TASKS_CARTOGRAPHY_2026_08.md). Шов литературы: [`TZ_SEAM_COVERAGE_MAP_2026_08.md`](TZ_SEAM_COVERAGE_MAP_2026_08.md). IUA: [`INTERPRETATION_USE_LEDGER_2026_08.md`](INTERPRETATION_USE_LEDGER_2026_08.md) строки `TL-04`…`TL-10`. Публичный бриф ТЗ v1 (6 стр.): [`../tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md`](../tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md) · `SAM-10`.

Checkpoint **`NO_GO`**. `detected_count: 0`.

## Этот проход (код)

Честные гейты, не «починить 0 правил extractor» и не поднять cap IFC:

1. Числовой `section_code` (том ПП-87) не подменяет `discipline` (3 ≠ АР).
2. `KR` в шифре принимается как КР; **KR не закрывает** обязательный слот `KZH`.
3. Нулевой QTO помещений — Missing экспорта, не Does-not против ТЭП.
4. Семь задач в исполняемом IUA-ledger (`TL-04`…`TL-10`).
5. SAM-TYP → номер задачи сравнения (scaffold; `customer_confirmed_patterns` остаётся 0).

Не делается: native RVT/NWD/LIRA, IDS `customer_approved`, закрытие RT-001/002/003, `summary.passed` от модели.

## Дальше (владелец + агент)

| Этап | Что | Стоп |
|---|---|---|
| A | Локальный манифест пакета; NDA не в git | sha256 пакета в git |
| B | Карта покрытия уже в git (v1.0.1, red-team) | Meets по задачам 1–7 |
| C | Комплектность = declared inventory; pairing PD↔RD fail без стадии РД | «87-ПП сертифицировано» |
| D | Семь задач как гипотезы; VLM advisory | DrawingVQA % как AeroBIM |
| E | Два разметчика + κ **или** честно «измерения нет» | PrecisionClaim.publishable без κ |
| F | КТ#3: CLI на фикстуре, `passed=false` | NDA в зал |
| G | ИОС IFC или MEP-OOS; стержни или OOS п.7; IDS назначающей стороны | Городской АГР = профиль Самолёта |

## DoD программы (не этого коммита)

КТ#3 без стоп-фразы. IUA и карта в git. Черновик EIR ≠ approved. κ или явный отказ от измерения. NO_GO пока RT-001/002b/003 OPEN.
