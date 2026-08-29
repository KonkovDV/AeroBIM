<!-- claims-lint: allow-file reason="PNST 841 AI quality eval mapping; not SQuaRE certification; NO_GO" -->
---
title: "PNST 841-2023 AI quality evaluation — mapping, not SQuaRE certification"
date: "2026-08-29"
last_updated: "2026-08-29"
status: active
version: "1.0.0"
closes_rt001: false
closes_rt002: false
closes_rt003: false
claim_boundary: >
  Preliminary national standard mapping. Not a certified SQuaRE assessment.
  Not product accuracy. Checkpoint NO_GO.
---

# ПНСТ 841-2023 — карта на уже стоящий протокол

**Предварительный** национальный стандарт (не ГОСТ Р). Приказ Росстандарта
16.11.2023 № **61-пнст** (ИСО/МЭК DTS 25058). Совместимость не оценка
соответствия SQuaRE. `pnst_841_certified() == False`.

Текст стандарта не копируется. Совпадение с тем, что уже есть:

| Тема ПНСТ 841 (смысл) | Уже в git |
|---|---|
| KPI и измерение функциональной корректности | Протокол классов; precision/recall раздельно |
| Экспертная оценка результатов | Dual-rater; HITL; ADR-001 |
| Разные / представительные наборы | Fixture ≠ партнёр; `is_representative=false` на обложке |
| Не «accuracy» на дисбалансе | F1 / TP-FP; не перенос ТЗ >90% |

Рядом: ПНСТ 965-2024 (тестирование систем ИИ, в т.ч. F1 вместо accuracy при
диспропорции классов) — тот же принцип, не сертификат тестирования.

Это аргумент **К2** (новизна измерения), не закрытие RT-001.
